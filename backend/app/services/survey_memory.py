"""
Survey Memory — Episodic, semantic, and reflective memory for survey agents.
"""

import json
import os
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('kinjeng.cognitive.memory')


@dataclass
class MemoryEntry:
    """A single memory entry."""
    timestamp: float
    type: str  # "episodic" | "semantic" | "reflective"
    content: str
    question_id: Optional[str] = None
    answer: Optional[str] = None
    likert_score: Optional[int] = None
    confidence: float = 0.0
    tags: List[str] = field(default_factory=list)


@dataclass
class AgentMemory:
    """Complete memory for one agent."""
    agent_id: str
    agent_name: str
    episodic: List[MemoryEntry] = field(default_factory=list)
    semantic: List[MemoryEntry] = field(default_factory=list)
    reflective: List[MemoryEntry] = field(default_factory=list)


class SurveyMemory:
    """
    Memory system for survey agents.
    
    Three memory types:
    - Episodic: What questions were asked and how the agent answered
    - Semantic: Facts and beliefs the agent holds
    - Reflective: Higher-level insights the agent has formed
    """
    
    MEMORY_DIR = os.path.join(Config.UPLOAD_FOLDER, 'survey_memories')
    
    def __init__(self, agent_id: str, agent_name: str = ""):
        self.agent_id = agent_id
        self.agent_name = agent_name or f"Agent-{agent_id}"
        self.episodic: List[MemoryEntry] = []
        self.semantic: List[MemoryEntry] = []
        self.reflective: List[MemoryEntry] = []
        self._dirty = False
        self._load()

    @classmethod
    def _ensure_dir(cls):
        os.makedirs(cls.MEMORY_DIR, exist_ok=True)

    def _memory_path(self) -> str:
        return os.path.join(self.MEMORY_DIR, f"{self.agent_id}.json")

    def _load(self):
        path = self._memory_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                for entry_list, key in [(self.episodic, "episodic"), (self.semantic, "semantic"), (self.reflective, "reflective")]:
                    for item in data.get(key, []):
                        entry_list.append(MemoryEntry(**item))
            except Exception as e:
                logger.warning(f"Failed to load memory for {self.agent_id}: {e}")

    def save(self):
        if not self._dirty:
            return
        self._ensure_dir()
        path = self._memory_path()
        data = {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "episodic": [vars(e) for e in self.episodic[-100:]],
            "semantic": [vars(e) for e in self.semantic[-50:]],
            "reflective": [vars(e) for e in self.reflective[-20:]]
        }
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._dirty = False

    def add_episodic(
        self,
        question: str,
        answer: str,
        question_id: Optional[str] = None,
        likert_score: Optional[int] = None,
        confidence: float = 0.0
    ):
        entry = MemoryEntry(
            timestamp=time.time(),
            type="episodic",
            content=question,
            question_id=question_id,
            answer=answer,
            likert_score=likert_score,
            confidence=confidence,
            tags=["episodic", "survey_response"]
        )
        self.episodic.append(entry)
        self._dirty = True

    def add_semantic(self, fact: str, tags: Optional[List[str]] = None):
        entry = MemoryEntry(
            timestamp=time.time(),
            type="semantic",
            content=fact,
            tags=tags or ["semantic", "belief"]
        )
        self.semantic.append(entry)
        self._dirty = True

    def add_reflective(self, insight: str, tags: Optional[List[str]] = None):
        entry = MemoryEntry(
            timestamp=time.time(),
            type="reflective",
            content=insight,
            tags=tags or ["reflective", "insight"]
        )
        self.reflective.append(entry)
        self._dirty = True

    def get_recent_episodic(self, count: int = 5) -> List[MemoryEntry]:
        return self.episodic[-count:]

    def get_recent_semantic(self, count: int = 3) -> List[MemoryEntry]:
        return self.semantic[-count:]

    def get_recent_reflective(self, count: int = 2) -> List[MemoryEntry]:
        return self.reflective[-count:]

    def get_consistency_check(self) -> Optional[str]:
        """Check if recent answers are consistent. Returns a summary or None."""
        recent = self.episodic[-5:]
        if len(recent) < 2:
            return None
        scores = [e.likert_score for e in recent if e.likert_score is not None]
        if len(scores) < 2:
            return None
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        if variance > 2.0:
            return f"Terdeteksi inkonsistensi dalam jawaban (variance={variance:.2f}). Partisipan mungkin tidak yakin."
        return None

    def get_context_block(self, max_items: int = 3) -> str:
        """Generate a context block for LLM prompts including recent memories."""
        parts = []
        recent_ep = self.get_recent_episodic(max_items)
        if recent_ep:
            parts.append("=== JAWABAN SEBELUMNYA ===")
            for e in recent_ep:
                score_str = f" (skor {e.likert_score})" if e.likert_score else ""
                parts.append(f"Q: {e.content}{score_str} → {e.answer}")

        recent_sem = self.get_recent_semantic(2)
        if recent_sem:
            parts.append("=== KEYAKINAN ===")
            for e in recent_sem:
                parts.append(f"- {e.content}")

        recent_ref = self.get_recent_reflective(1)
        if recent_ref:
            parts.append("=== REFLEKSI ===")
            for e in recent_ref:
                parts.append(f"- {e.content}")

        return "\n".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "episodic_count": len(self.episodic),
            "semantic_count": len(self.semantic),
            "reflective_count": len(self.reflective),
            "recent_episodic": [vars(e) for e in self.episodic[-5:]],
            "recent_semantic": [vars(e) for e in self.semantic[-3:]],
            "recent_reflective": [vars(e) for e in self.reflective[-2:]]
        }


class SurveyMemoryStore:
    """Manages memory for all survey agents."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self._cache: Dict[str, SurveyMemory] = {}

    def get(self, agent_id: str, agent_name: str = "") -> SurveyMemory:
        if agent_id not in self._cache:
            self._cache[agent_id] = SurveyMemory(agent_id, agent_name)
        return self._cache[agent_id]

    def save_all(self):
        for mem in self._cache.values():
            mem.save()

    def get_all_memories(self) -> List[Dict[str, Any]]:
        return [mem.to_dict() for mem in self._cache.values()]
