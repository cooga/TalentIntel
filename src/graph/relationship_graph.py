"""Relationship Graph for talent network visualization and analysis."""

from datetime import datetime
from enum import Enum
from typing import Any
from dataclasses import dataclass, field
import hashlib
import json

import structlog

logger = structlog.get_logger()


class NodeType(str, Enum):
    """Types of nodes in the relationship graph."""
    PERSON = "person"
    COMPANY = "company"
    ORGANIZATION = "organization"
    TECHNOLOGY = "technology"
    PROJECT = "project"
    EVENT = "event"


class EdgeType(str, Enum):
    """Types of edges in the relationship graph."""
    WORKS_AT = "works_at"
    WORKED_AT = "worked_at"
    FOLLOWS = "follows"
    KNOWS = "knows"
    CONTRIBUTES_TO = "contributes_to"
    MENTIONS = "mentions"
    CO_OCCURS = "co_occurs"
    SAME_COMPANY = "same_company"
    COLLABORATES = "collaborates"


@dataclass
class GraphNode:
    """Represents a node in the relationship graph."""
    id: str
    type: NodeType
    label: str
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert node to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "label": self.label,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
        }

    def to_cytoscape(self) -> dict[str, Any]:
        """Convert to Cytoscape.js format."""
        return {
            "data": {
                "id": self.id,
                "label": self.label,
                "type": self.type.value,
                **self.properties,
            }
        }


@dataclass
class GraphEdge:
    """Represents an edge in the relationship graph."""
    id: str
    source: str
    target: str
    type: EdgeType
    weight: float = 1.0
    properties: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict[str, Any]:
        """Convert edge to dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "type": self.type.value,
            "weight": self.weight,
            "properties": self.properties,
            "created_at": self.created_at.isoformat(),
        }

    def to_cytoscape(self) -> dict[str, Any]:
        """Convert to Cytoscape.js format."""
        return {
            "data": {
                "id": self.id,
                "source": self.source,
                "target": self.target,
                "type": self.type.value,
                "weight": self.weight,
                **self.properties,
            }
        }


class RelationshipGraph:
    """In-memory relationship graph for talent network analysis."""

    def __init__(self) -> None:
        """Initialize the relationship graph."""
        self.nodes: dict[str, GraphNode] = {}
        self.edges: dict[str, GraphEdge] = {}
        self._adjacency: dict[str, set[str]] = {}  # node_id -> set of connected node_ids

    def add_node(
        self,
        node_id: str,
        node_type: NodeType,
        label: str,
        properties: dict[str, Any] | None = None,
    ) -> GraphNode:
        """Add a node to the graph.

        Args:
            node_id: Unique identifier for the node.
            node_type: Type of the node.
            label: Display label for the node.
            properties: Optional additional properties.

        Returns:
            The created or existing node.
        """
        if node_id in self.nodes:
            # Update existing node
            node = self.nodes[node_id]
            if properties:
                node.properties.update(properties)
            return node

        node = GraphNode(
            id=node_id,
            type=node_type,
            label=label,
            properties=properties or {},
        )
        self.nodes[node_id] = node
        self._adjacency[node_id] = set()

        logger.debug("node_added", node_id=node_id, type=node_type.value)
        return node

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
        weight: float = 1.0,
        properties: dict[str, Any] | None = None,
    ) -> GraphEdge | None:
        """Add an edge to the graph.

        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            edge_type: Type of the edge.
            weight: Edge weight (importance).
            properties: Optional additional properties.

        Returns:
            The created edge, or None if nodes don't exist.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            logger.warning(
                "edge_nodes_not_found",
                source=source_id,
                target=target_id,
            )
            return None

        edge_id = self._generate_edge_id(source_id, target_id, edge_type)

        if edge_id in self.edges:
            # Update existing edge
            edge = self.edges[edge_id]
            edge.weight = max(edge.weight, weight)
            if properties:
                edge.properties.update(properties)
            return edge

        edge = GraphEdge(
            id=edge_id,
            source=source_id,
            target=target_id,
            type=edge_type,
            weight=weight,
            properties=properties or {},
        )
        self.edges[edge_id] = edge
        self._adjacency[source_id].add(target_id)
        self._adjacency[target_id].add(source_id)

        logger.debug(
            "edge_added",
            edge_id=edge_id,
            source=source_id,
            target=target_id,
            type=edge_type.value,
        )
        return edge

    def get_node(self, node_id: str) -> GraphNode | None:
        """Get a node by ID."""
        return self.nodes.get(node_id)

    def get_edge(self, source_id: str, target_id: str, edge_type: EdgeType) -> GraphEdge | None:
        """Get an edge by source, target, and type."""
        edge_id = self._generate_edge_id(source_id, target_id, edge_type)
        return self.edges.get(edge_id)

    def get_neighbors(self, node_id: str) -> list[GraphNode]:
        """Get all neighboring nodes."""
        if node_id not in self._adjacency:
            return []
        return [
            self.nodes[nid]
            for nid in self._adjacency[node_id]
            if nid in self.nodes
        ]

    def get_edges_for_node(self, node_id: str) -> list[GraphEdge]:
        """Get all edges connected to a node."""
        return [
            edge for edge in self.edges.values()
            if edge.source == node_id or edge.target == node_id
        ]

    def get_nodes_by_type(self, node_type: NodeType) -> list[GraphNode]:
        """Get all nodes of a specific type."""
        return [
            node for node in self.nodes.values()
            if node.type == node_type
        ]

    def get_edges_by_type(self, edge_type: EdgeType) -> list[GraphEdge]:
        """Get all edges of a specific type."""
        return [
            edge for edge in self.edges.values()
            if edge.type == edge_type
        ]

    def find_path(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 3,
    ) -> list[str] | None:
        """Find shortest path between two nodes using BFS.

        Args:
            source_id: Starting node ID.
            target_id: Target node ID.
            max_depth: Maximum search depth.

        Returns:
            List of node IDs forming the path, or None if no path found.
        """
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        if source_id == target_id:
            return [source_id]

        visited = {source_id}
        queue = [(source_id, [source_id])]

        while queue:
            current, path = queue.pop(0)

            if len(path) > max_depth:
                continue

            for neighbor_id in self._adjacency.get(current, set()):
                if neighbor_id in visited:
                    continue

                new_path = path + [neighbor_id]

                if neighbor_id == target_id:
                    return new_path

                visited.add(neighbor_id)
                queue.append((neighbor_id, new_path))

        return None

    def get_subgraph(
        self,
        center_id: str,
        depth: int = 2,
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Get a subgraph centered on a node.

        Args:
            center_id: Center node ID.
            depth: How many hops to include.

        Returns:
            Tuple of (nodes, edges) in the subgraph.
        """
        if center_id not in self.nodes:
            return [], []

        included_nodes = {center_id}
        frontier = {center_id}

        for _ in range(depth):
            new_frontier = set()
            for node_id in frontier:
                new_frontier.update(self._adjacency.get(node_id, set()))
            included_nodes.update(new_frontier)
            frontier = new_frontier

        nodes = [self.nodes[nid] for nid in included_nodes if nid in self.nodes]
        edges = [
            edge for edge in self.edges.values()
            if edge.source in included_nodes and edge.target in included_nodes
        ]

        return nodes, edges

    def to_dict(self) -> dict[str, Any]:
        """Export graph to dictionary format."""
        return {
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()],
            "metadata": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
                "exported_at": datetime.utcnow().isoformat(),
            },
        }

    def to_cytoscape(self) -> dict[str, Any]:
        """Export to Cytoscape.js format for visualization."""
        return {
            "elements": {
                "nodes": [node.to_cytoscape() for node in self.nodes.values()],
                "edges": [edge.to_cytoscape() for edge in self.edges.values()],
            },
            "metadata": {
                "node_count": len(self.nodes),
                "edge_count": len(self.edges),
            },
        }

    def clear(self) -> None:
        """Clear the graph."""
        self.nodes.clear()
        self.edges.clear()
        self._adjacency.clear()

    def _generate_edge_id(
        self,
        source_id: str,
        target_id: str,
        edge_type: EdgeType,
    ) -> str:
        """Generate a unique edge ID."""
        content = f"{source_id}:{target_id}:{edge_type.value}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
