"""
Entity-related functions for Zep graph (reading, filtering, detail lookup)
"""

from typing import Dict, Any, List, Optional

from ...config import Config
from ...utils.logger import get_logger
from ...utils.locale import t
from ...utils.zep_paging import fetch_all_nodes, fetch_all_edges

from . import NodeInfo, EdgeInfo

logger = get_logger('mirofish.zep_tools.entities')


class EntitiesMixin:
    """Mixin with entity lookup methods for ZepToolsService."""

    def get_all_nodes(self, graph_id: str) -> List[NodeInfo]:
        logger.info(t("console.fetchingAllNodes", graphId=graph_id))

        if self._nodes_data is not None:
            result = []
            for n in self._nodes_data:
                result.append(NodeInfo(
                    uuid=n.get("uuid", ""),
                    name=n.get("name", ""),
                    labels=n.get("labels", []),
                    summary=n.get("summary", ""),
                    attributes=n.get("attributes", {})
                ))
            logger.info(t("console.fetchedNodes", count=len(result)))
            return result

        nodes = fetch_all_nodes(self.client, graph_id)

        result = []
        for node in nodes:
            node_uuid = getattr(node, 'uuid_', None) or getattr(node, 'uuid', None) or ""
            result.append(NodeInfo(
                uuid=str(node_uuid) if node_uuid else "",
                name=node.name or "",
                labels=node.labels or [],
                summary=node.summary or "",
                attributes=node.attributes or {}
            ))

        logger.info(t("console.fetchedNodes", count=len(result)))
        return result

    def get_all_edges(self, graph_id: str, include_temporal: bool = True) -> List[EdgeInfo]:
        logger.info(t("console.fetchingAllEdges", graphId=graph_id))

        if self._edges_data is not None:
            result = []
            for e in self._edges_data:
                edge_info = EdgeInfo(
                    uuid=e.get("uuid", ""),
                    name=e.get("name", "") or e.get("fact_type", ""),
                    fact=e.get("fact", ""),
                    source_node_uuid=e.get("source_node_uuid", ""),
                    target_node_uuid=e.get("target_node_uuid", ""),
                    source_node_name=e.get("source_node_name", ""),
                    target_node_name=e.get("target_node_name", "")
                )
                if include_temporal:
                    edge_info.created_at = e.get("created_at")
                    edge_info.valid_at = e.get("valid_at")
                    edge_info.invalid_at = e.get("invalid_at")
                    edge_info.expired_at = e.get("expired_at")
                result.append(edge_info)
            logger.info(t("console.fetchedEdges", count=len(result)))
            return result

        edges = fetch_all_edges(self.client, graph_id)

        result = []
        for edge in edges:
            edge_uuid = getattr(edge, 'uuid_', None) or getattr(edge, 'uuid', None) or ""
            edge_info = EdgeInfo(
                uuid=str(edge_uuid) if edge_uuid else "",
                name=edge.name or "",
                fact=edge.fact or "",
                source_node_uuid=edge.source_node_uuid or "",
                target_node_uuid=edge.target_node_uuid or ""
            )

            if include_temporal:
                edge_info.created_at = getattr(edge, 'created_at', None)
                edge_info.valid_at = getattr(edge, 'valid_at', None)
                edge_info.invalid_at = getattr(edge, 'invalid_at', None)
                edge_info.expired_at = getattr(edge, 'expired_at', None)

            result.append(edge_info)

        logger.info(t("console.fetchedEdges", count=len(result)))
        return result

    def get_node_detail(self, node_uuid: str) -> Optional[NodeInfo]:
        logger.info(t("console.fetchingNodeDetail", uuid=node_uuid[:8]))

        if self._nodes_data is not None:
            for n in self._nodes_data:
                if n.get("uuid") == node_uuid:
                    return NodeInfo(
                        uuid=n.get("uuid", ""),
                        name=n.get("name", ""),
                        labels=n.get("labels", []),
                        summary=n.get("summary", ""),
                        attributes=n.get("attributes", {})
                    )
            return None

        try:
            node = self._call_with_retry(
                func=lambda: self.client.graph.node.get(uuid_=node_uuid),
                operation_name=t("console.fetchNodeDetailOp", uuid=node_uuid[:8])
            )

            if not node:
                return None

            return NodeInfo(
                uuid=getattr(node, 'uuid_', None) or getattr(node, 'uuid', ''),
                name=node.name or "",
                labels=node.labels or [],
                summary=node.summary or "",
                attributes=node.attributes or {}
            )
        except Exception as e:
            logger.error(t("console.fetchNodeDetailFailed", error=str(e)))
            return None

    def get_node_edges(self, graph_id: str, node_uuid: str) -> List[EdgeInfo]:
        logger.info(t("console.fetchingNodeEdges", uuid=node_uuid[:8]))

        try:
            all_edges = self.get_all_edges(graph_id)

            result = []
            for edge in all_edges:
                if edge.source_node_uuid == node_uuid or edge.target_node_uuid == node_uuid:
                    result.append(edge)

            logger.info(t("console.foundNodeEdges", count=len(result)))
            return result

        except Exception as e:
            logger.warning(t("console.fetchNodeEdgesFailed", error=str(e)))
            return []

    def get_entities_by_type(
        self,
        graph_id: str,
        entity_type: str
    ) -> List[NodeInfo]:
        logger.info(t("console.fetchingEntitiesByType", type=entity_type))

        all_nodes = self.get_all_nodes(graph_id)

        filtered = []
        for node in all_nodes:
            if entity_type in node.labels:
                filtered.append(node)

        logger.info(t("console.foundEntitiesByType", count=len(filtered), type=entity_type))
        return filtered

    def get_entity_summary(
        self,
        graph_id: str,
        entity_name: str
    ) -> Dict[str, Any]:
        logger.info(t("console.fetchingEntitySummary", name=entity_name))

        search_result = self.search_graph(
            graph_id=graph_id,
            query=entity_name,
            limit=20
        )

        all_nodes = self.get_all_nodes(graph_id)
        entity_node = None
        for node in all_nodes:
            if node.name.lower() == entity_name.lower():
                entity_node = node
                break

        related_edges = []
        if entity_node:
            related_edges = self.get_node_edges(graph_id, entity_node.uuid)

        return {
            "entity_name": entity_name,
            "entity_info": entity_node.to_dict() if entity_node else None,
            "related_facts": search_result.facts,
            "related_edges": [e.to_dict() for e in related_edges],
            "total_relations": len(related_edges)
        }
