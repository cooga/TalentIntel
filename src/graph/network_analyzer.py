"""Network Analyzer for relationship graph analysis."""

from collections import defaultdict
from typing import Any
from dataclasses import dataclass, field

import structlog

from src.graph.relationship_graph import (
    RelationshipGraph,
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
)

logger = structlog.get_logger()


@dataclass
class CentralityScores:
    """Centrality scores for a node."""
    node_id: str
    degree_centrality: float = 0.0
    betweenness_centrality: float = 0.0
    closeness_centrality: float = 0.0
    eigenvector_centrality: float = 0.0


@dataclass
class Community:
    """Represents a detected community."""
    community_id: int
    nodes: list[str]
    size: int
    density: float = 0.0
    label: str = ""


@dataclass
class ProximityAlert:
    """Alert for unusual proximity changes."""
    entity_id: str
    target_company: str
    proximity_change: float
    confidence: float
    evidence: dict[str, Any] = field(default_factory=dict)


class NetworkAnalyzer:
    """Analyzer for relationship network insights."""

    def __init__(self, graph: RelationshipGraph) -> None:
        """Initialize network analyzer.

        Args:
            graph: The relationship graph to analyze.
        """
        self.graph = graph

    def calculate_degree_centrality(self) -> dict[str, float]:
        """Calculate degree centrality for all nodes.

        Returns:
            Dictionary mapping node_id to centrality score.
        """
        if not self.graph.nodes:
            return {}

        max_possible_degree = len(self.graph.nodes) - 1
        if max_possible_degree == 0:
            return {nid: 0.0 for nid in self.graph.nodes}

        scores = {}
        for node_id in self.graph.nodes:
            degree = len(self.graph.get_neighbors(node_id))
            scores[node_id] = degree / max_possible_degree

        return scores

    def calculate_betweenness_centrality(self) -> dict[str, float]:
        """Calculate betweenness centrality using Brandes' algorithm.

        Returns:
            Dictionary mapping node_id to betweenness score.
        """
        if len(self.graph.nodes) < 3:
            return {nid: 0.0 for nid in self.graph.nodes}

        betweenness = defaultdict(float)

        for source_id in self.graph.nodes:
            # BFS to find shortest paths
            predecessors = defaultdict(list)
            shortest_paths = {source_id: 1}
            distances = {source_id: 0}
            stack = []
            queue = [source_id]

            while queue:
                current = queue.pop(0)
                stack.append(current)

                for neighbor in self.graph.get_neighbors(current):
                    neighbor_id = neighbor.id

                    if neighbor_id not in distances:
                        distances[neighbor_id] = distances[current] + 1
                        queue.append(neighbor_id)

                    if distances[neighbor_id] == distances[current] + 1:
                        shortest_paths[neighbor_id] = shortest_paths.get(neighbor_id, 0) + shortest_paths[current]
                        predecessors[neighbor_id].append(current)

            # Back-propagation
            dependency = defaultdict(float)
            while stack:
                current = stack.pop()
                for pred in predecessors[current]:
                    dependency[pred] += (
                        shortest_paths[pred] / shortest_paths[current]
                    ) * (1 + dependency[current])
                if current != source_id:
                    betweenness[current] += dependency[current]

        # Normalize
        n = len(self.graph.nodes)
        norm_factor = (n - 1) * (n - 2) / 2 if n > 2 else 1

        return {
            node_id: score / norm_factor
            for node_id, score in betweenness.items()
        }

    def find_key_players(self, top_n: int = 10) -> list[dict[str, Any]]:
        """Find the most important nodes in the network.

        Args:
            top_n: Number of top players to return.

        Returns:
            List of key player information.
        """
        degree_scores = self.calculate_degree_centrality()

        # Combine scores
        combined_scores = []
        for node_id, score in degree_scores.items():
            node = self.graph.get_node(node_id)
            if node and node.type == NodeType.PERSON:
                combined_scores.append({
                    "node_id": node_id,
                    "label": node.label,
                    "centrality": score,
                    "connections": len(self.graph.get_neighbors(node_id)),
                })

        # Sort by centrality
        combined_scores.sort(key=lambda x: x["centrality"], reverse=True)
        return combined_scores[:top_n]

    def detect_communities(self) -> list[Community]:
        """Detect communities using label propagation algorithm.

        Returns:
            List of detected communities.
        """
        if not self.graph.nodes:
            return []

        # Initialize: each node has its own label
        labels = {node_id: i for i, node_id in enumerate(self.graph.nodes)}

        # Iterate until convergence
        changed = True
        max_iterations = 100
        iteration = 0

        while changed and iteration < max_iterations:
            changed = False
            iteration += 1

            for node_id in list(labels.keys()):
                neighbors = self.graph.get_neighbors(node_id)
                if not neighbors:
                    continue

                # Count neighbor labels
                neighbor_labels = defaultdict(int)
                for neighbor in neighbors:
                    neighbor_labels[labels[neighbor.id]] += 1

                # Find most common label
                if neighbor_labels:
                    max_count = max(neighbor_labels.values())
                    candidates = [
                        label for label, count in neighbor_labels.items()
                        if count == max_count
                    ]
                    new_label = min(candidates)  # Deterministic tie-breaking

                    if labels[node_id] != new_label:
                        labels[node_id] = new_label
                        changed = True

        # Group nodes by community
        communities_map = defaultdict(list)
        for node_id, label in labels.items():
            communities_map[label].append(node_id)

        # Create Community objects
        communities = []
        for i, (label, node_ids) in enumerate(communities_map.items()):
            community = Community(
                community_id=i,
                nodes=node_ids,
                size=len(node_ids),
                density=self._calculate_community_density(node_ids),
            )
            communities.append(community)

        # Sort by size
        communities.sort(key=lambda c: c.size, reverse=True)
        return communities

    def find_connections_between(
        self,
        source_id: str,
        target_id: str,
        max_depth: int = 4,
    ) -> list[dict[str, Any]]:
        """Find all paths between two nodes.

        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            max_depth: Maximum path length.

        Returns:
            List of paths with details.
        """
        path = self.graph.find_path(source_id, target_id, max_depth)
        if not path:
            return []

        # Build path details
        path_nodes = []
        for node_id in path:
            node = self.graph.get_node(node_id)
            if node:
                path_nodes.append({
                    "id": node_id,
                    "label": node.label,
                    "type": node.type.value,
                })

        return [{
            "length": len(path) - 1,
            "nodes": path_nodes,
            "path": " → ".join(n["label"] for n in path_nodes),
        }]

    def analyze_company_proximity(
        self,
        entity_id: str,
        company_nodes: list[str],
    ) -> ProximityAlert | None:
        """Analyze proximity between an entity and company nodes.

        Args:
            entity_id: Entity node ID.
            company_nodes: List of company node IDs.

        Returns:
            ProximityAlert if significant proximity detected.
        """
        entity = self.graph.get_node(entity_id)
        if not entity:
            return None

        # Count connections to company nodes
        neighbors = self.graph.get_neighbors(entity_id)
        company_connections = [
            n for n in neighbors
            if n.id in company_nodes or
               (n.type == NodeType.COMPANY and n.label.lower() in [c.lower() for c in company_nodes])
        ]

        if not company_connections:
            return None

        proximity_score = len(company_connections) / max(len(neighbors), 1)

        if proximity_score > 0.3:  # 30% of connections are to target company
            return ProximityAlert(
                entity_id=entity_id,
                target_company=company_connections[0].label if company_connections else "Unknown",
                proximity_change=proximity_score,
                confidence=min(0.5 + proximity_score, 0.95),
                evidence={
                    "company_connections": [n.label for n in company_connections],
                    "total_connections": len(neighbors),
                },
            )

        return None

    def get_network_statistics(self) -> dict[str, Any]:
        """Get overall network statistics.

        Returns:
            Dictionary of network statistics.
        """
        if not self.graph.nodes:
            return {"error": "Empty graph"}

        # Basic stats
        stats = {
            "node_count": len(self.graph.nodes),
            "edge_count": len(self.graph.edges),
            "density": self._calculate_density(),
            "node_types": {},
            "edge_types": {},
        }

        # Count node types
        for node in self.graph.nodes.values():
            type_name = node.type.value
            stats["node_types"][type_name] = stats["node_types"].get(type_name, 0) + 1

        # Count edge types
        for edge in self.graph.edges.values():
            type_name = edge.type.value
            stats["edge_types"][type_name] = stats["edge_types"].get(type_name, 0) + 1

        # Centrality stats
        degree_scores = self.calculate_degree_centrality()
        if degree_scores:
            stats["avg_centrality"] = sum(degree_scores.values()) / len(degree_scores)
            stats["max_centrality"] = max(degree_scores.values())

        # Community stats
        communities = self.detect_communities()
        if communities:
            stats["community_count"] = len(communities)
            stats["largest_community_size"] = communities[0].size if communities else 0

        return stats

    def _calculate_density(self) -> float:
        """Calculate graph density."""
        n = len(self.graph.nodes)
        if n < 2:
            return 0.0

        max_edges = n * (n - 1)
        if max_edges == 0:
            return 0.0

        return len(self.graph.edges) / max_edges

    def _calculate_community_density(self, node_ids: list[str]) -> float:
        """Calculate density within a community."""
        if len(node_ids) < 2:
            return 0.0

        internal_edges = 0
        for edge in self.graph.edges.values():
            if edge.source in node_ids and edge.target in node_ids:
                internal_edges += 1

        max_possible = len(node_ids) * (len(node_ids) - 1)
        return internal_edges / max_possible if max_possible > 0 else 0.0
