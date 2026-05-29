import json
import os
import uuid
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional

from ..config import Config
from ..utils.llm_client import LLMClient
from ..utils.logger import get_logger

logger = get_logger('kinjeng.local_graph')

GRAPHS_DIR = os.path.join(os.path.dirname(__file__), '../data/graphs')

# Simple in-memory LLM response cache (LRU, max 256 entries)
_llm_cache: Dict[str, Dict] = {}
_MAX_CACHE = 256


def _cache_key(prompt: str) -> str:
    return hashlib.md5(prompt.encode()).hexdigest()


def _get_cached(prompt: str) -> Optional[Dict]:
    key = _cache_key(prompt)
    return _llm_cache.get(key)


def _set_cache(prompt: str, result: Dict):
    key = _cache_key(prompt)
    if len(_llm_cache) >= _MAX_CACHE:
        # Remove oldest entry
        oldest = next(iter(_llm_cache))
        del _llm_cache[oldest]
    _llm_cache[key] = result


class LocalGraphStore:
    """Local JSON-based graph storage with LLM entity extraction"""

    def __init__(self):
        os.makedirs(GRAPHS_DIR, exist_ok=True)

    def create(self, graph_id: str, name: str, description: str = ""):
        path = os.path.join(GRAPHS_DIR, f"{graph_id}.json")
        if os.path.exists(path):
            return
        data = {
            "graph_id": graph_id,
            "name": name,
            "description": description,
            "nodes": [],
            "edges": [],
            "node_count": 0,
            "edge_count": 0,
            "entity_types": [],
            "created_at": time.time()
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def delete(self, graph_id: str):
        path = os.path.join(GRAPHS_DIR, f"{graph_id}.json")
        if os.path.exists(path):
            os.remove(path)

    def load(self, graph_id: str) -> Optional[Dict[str, Any]]:
        path = os.path.join(GRAPHS_DIR, f"{graph_id}.json")
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save(self, data: Dict[str, Any]):
        path = os.path.join(GRAPHS_DIR, f"{data['graph_id']}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def extract_entities(self, chunks: List[str], ontology: Dict[str, Any]) -> tuple:
        """Extract entities + edges from text chunks via LLM (batched: multiple chunks per call)"""
        llm = LLMClient()
        entity_type_names = [e["name"] for e in ontology.get("entity_types", [])]
        edge_type_names = [e["name"] for e in ontology.get("edge_types", [])]

        all_nodes = []
        all_edges = []
        seen_nodes = {}
        BATCH_SIZE = 5

        def _process_batch(batch: List[str], batch_idx: int):
            labeled = "\n\n".join(
                f"[Chunk {batch_idx + idx + 1}]\n{chunk}" for idx, chunk in enumerate(batch)
            )
            prompt = f"""Extract entities and relationships from these text chunks as JSON.

Allowed entity types: {json.dumps(entity_type_names)}
Allowed relationship types: {json.dumps(edge_type_names)}

Rules:
- Entity: name, type (from allowed), summary (1 sentence max)
- Relationship: source, target, type (from allowed), fact (1 sentence)
- Use ONLY allowed types. Deduplicate entities with same name.

JSON: {{"entities": [{{"name","type","summary"}}], "relationships": [{{"source","target","type","fact"}}]}}

Chunks:
{labeled}"""

            cached = _get_cached(prompt)
            if cached:
                logger.info(f"Batch {batch_idx}: cache HIT")
                return cached

            try:
                result = llm.chat_json(
                    [{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=2048
                )
                _set_cache(prompt, result)
                return result
            except Exception as e:
                logger.warning(f"LLM extraction failed for batch {batch_idx}: {e}")
                return {"entities": [], "relationships": []}

        batches = [chunks[i:i+BATCH_SIZE] for i in range(0, len(chunks), BATCH_SIZE)]
        results = [None] * len(batches)

        with ThreadPoolExecutor(max_workers=4) as executor:
            future_map = {
                executor.submit(_process_batch, batch, i): i
                for i, batch in enumerate(batches)
            }
            for future in as_completed(future_map):
                i = future_map[future]
                try:
                    results[i] = future.result(timeout=60)
                except Exception as e:
                    logger.warning(f"Batch {i} unexpected error: {e}")
                    results[i] = {"entities": [], "relationships": []}

        for result in results:
            for ent in result.get("entities", []):
                name = ent["name"].strip()
                if name not in seen_nodes:
                    node_uuid = str(uuid.uuid4())
                    seen_nodes[name] = node_uuid
                    all_nodes.append({
                        "uuid": node_uuid,
                        "name": name,
                        "labels": [ent.get("type", "Entity")],
                        "summary": ent.get("summary", ""),
                        "attributes": {},
                        "created_at": time.time()
                    })
                for rel in result.get("relationships", []):
                    src = rel["source"].strip()
                    tgt = rel["target"].strip()
                    if src in seen_nodes and tgt in seen_nodes:
                        all_edges.append({
                            "uuid": str(uuid.uuid4()),
                            "name": rel.get("type", ""),
                            "fact": rel.get("fact", ""),
                            "fact_type": rel.get("type", ""),
                            "source_node_uuid": seen_nodes[src],
                            "target_node_uuid": seen_nodes[tgt],
                            "source_node_name": src,
                            "target_node_name": tgt,
                            "attributes": {},
                            "created_at": time.time()
                        })

        return all_nodes, all_edges

    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        data = self.load(graph_id)
        if not data:
            return {
                "graph_id": graph_id,
                "nodes": [],
                "edges": [],
                "node_count": 0,
                "edge_count": 0
            }
        return {
            "graph_id": graph_id,
            "nodes": data.get("nodes", []),
            "edges": data.get("edges", []),
            "node_count": len(data.get("nodes", [])),
            "edge_count": len(data.get("edges", []))
        }

    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        data = self.load(graph_id)
        if data:
            data["entity_types"] = list(ontology.get("entity_types", []))
            self.save(data)

    def add_text_batches(self, graph_id: str, chunks: List[str], ontology: Dict[str, Any],
                         progress_callback=None, batch_size: int = 3):
        data = self.load(graph_id)
        if not data:
            return []

        nodes, edges = self.extract_entities(chunks, ontology)

        existing_names = {n["name"] for n in data.get("nodes", [])}
        for n in nodes:
            if n["name"] not in existing_names:
                data["nodes"].append(n)
                existing_names.add(n["name"])

        existing_edge_uuids = {e["uuid"] for e in data.get("edges", [])}
        for e in edges:
            if e["uuid"] not in existing_edge_uuids:
                data["edges"].append(e)

        data["node_count"] = len(data["nodes"])
        data["edge_count"] = len(data["edges"])
        self.save(data)

        if progress_callback:
            progress_callback("Local graph updated with LLM-extracted entities.", 1.0)

        return []
