"""Tests for relationship graph module."""

import pytest
from datetime import datetime

from src.graph.relationship_graph import (
    RelationshipGraph,
    GraphNode,
    GraphEdge,
    NodeType,
    EdgeType,
)
from src.graph.network_analyzer import (
    NetworkAnalyzer,
    CentralityScores,
    Community,
    ProximityAlert,
)


class TestRelationshipGraph:
    """Tests for RelationshipGraph."""

    def test_add_node(self):
        """Test adding a node to the graph."""
        graph = RelationshipGraph()
        node = graph.add_node(
            node_id="person_1",
            node_type=NodeType.PERSON,
            label="John Doe",
            properties={"company": "Acme Corp"},
        )

        assert node.id == "person_1"
        assert node.type == NodeType.PERSON
        assert node.label == "John Doe"
        assert node.properties["company"] == "Acme Corp"
        assert len(graph.nodes) == 1

    def test_add_node_update_existing(self):
        """Test updating an existing node."""
        graph = RelationshipGraph()
        graph.add_node("person_1", NodeType.PERSON, "John Doe")

        # Add again with new properties
        node = graph.add_node(
            "person_1",
            NodeType.PERSON,
            "John Doe",
            properties={"company": "New Corp"},
        )

        assert node.properties["company"] == "New Corp"
        assert len(graph.nodes) == 1

    def test_add_edge(self):
        """Test adding an edge to the graph."""
        graph = RelationshipGraph()
        graph.add_node("person_1", NodeType.PERSON, "John")
        graph.add_node("company_1", NodeType.COMPANY, "Acme")

        edge = graph.add_edge(
            source_id="person_1",
            target_id="company_1",
            edge_type=EdgeType.WORKS_AT,
        )

        assert edge is not None
        assert edge.source == "person_1"
        assert edge.target == "company_1"
        assert edge.type == EdgeType.WORKS_AT
        assert len(graph.edges) == 1

    def test_add_edge_missing_nodes(self):
        """Test adding edge with missing nodes returns None."""
        graph = RelationshipGraph()
        edge = graph.add_edge("person_1", "company_1", EdgeType.WORKS_AT)
        assert edge is None

    def test_get_neighbors(self):
        """Test getting neighbors."""
        graph = RelationshipGraph()
        graph.add_node("p1", NodeType.PERSON, "Person 1")
        graph.add_node("p2", NodeType.PERSON, "Person 2")
        graph.add_node("p3", NodeType.PERSON, "Person 3")
        graph.add_edge("p1", "p2", EdgeType.KNOWS)
        graph.add_edge("p1", "p3", EdgeType.KNOWS)

        neighbors = graph.get_neighbors("p1")
        assert len(neighbors) == 2

    def test_find_path_direct(self):
        """Test finding direct path."""
        graph = RelationshipGraph()
        graph.add_node("p1", NodeType.PERSON, "Person 1")
        graph.add_node("p2", NodeType.PERSON, "Person 2")
        graph.add_edge("p1", "p2", EdgeType.KNOWS)

        path = graph.find_path("p1", "p2")
        assert path == ["p1", "p2"]

    def test_find_path_multi_hop(self):
        """Test finding multi-hop path."""
        graph = RelationshipGraph()
        graph.add_node("p1", NodeType.PERSON, "Person 1")
        graph.add_node("p2", NodeType.PERSON, "Person 2")
        graph.add_node("p3", NodeType.PERSON, "Person 3")
        graph.add_edge("p1", "p2", EdgeType.KNOWS)
        graph.add_edge("p2", "p3", EdgeType.KNOWS)

        path = graph.find_path("p1", "p3")
        assert path == ["p1", "p2", "p3"]

    def test_find_path_no_path(self):
        """Test when no path exists."""
        graph = RelationshipGraph()
        graph.add_node("p1", NodeType.PERSON, "Person 1")
        graph.add_node("p2", NodeType.PERSON, "Person 2")

        path = graph.find_path("p1", "p2")
        assert path is None

    def test_get_subgraph(self):
        """Test getting subgraph."""
        graph = RelationshipGraph()
        graph.add_node("p1", NodeType.PERSON, "Person 1")
        graph.add_node("p2", NodeType.PERSON, "Person 2")
        graph.add_node("p3", NodeType.PERSON, "Person 3")
        graph.add_node("p4", NodeType.PERSON, "Person 4")
        graph.add_edge("p1", "p2", EdgeType.KNOWS)
        graph.add_edge("p2", "p3", EdgeType.KNOWS)
        graph.add_edge("p3", "p4", EdgeType.KNOWS)

        nodes, edges = graph.get_subgraph("p1", depth=1)
        assert len(nodes) == 2  # p1 and p2

        nodes, edges = graph.get_subgraph("p1", depth=2)
        assert len(nodes) == 3  # p1, p2, p3

    def test_to_cytoscape(self):
        """Test exporting to Cytoscape format."""
        graph = RelationshipGraph()
        graph.add_node("p1", NodeType.PERSON, "Person 1")
        graph.add_node("c1", NodeType.COMPANY, "Company")
        graph.add_edge("p1", "c1", EdgeType.WORKS_AT)

        cyto = graph.to_cytoscape()

        assert "elements" in cyto
        assert len(cyto["elements"]["nodes"]) == 2
        assert len(cyto["elements"]["edges"]) == 1

    def test_get_nodes_by_type(self):
        """Test filtering nodes by type."""
        graph = RelationshipGraph()
        graph.add_node("p1", NodeType.PERSON, "Person 1")
        graph.add_node("p2", NodeType.PERSON, "Person 2")
        graph.add_node("c1", NodeType.COMPANY, "Company")

        persons = graph.get_nodes_by_type(NodeType.PERSON)
        assert len(persons) == 2

        companies = graph.get_nodes_by_type(NodeType.COMPANY)
        assert len(companies) == 1


class TestNetworkAnalyzer:
    """Tests for NetworkAnalyzer."""

    @pytest.fixture
    def sample_graph(self):
        """Create sample graph for testing."""
        graph = RelationshipGraph()

        # Create a simple network
        graph.add_node("p1", NodeType.PERSON, "Person 1")
        graph.add_node("p2", NodeType.PERSON, "Person 2")
        graph.add_node("p3", NodeType.PERSON, "Person 3")
        graph.add_node("c1", NodeType.COMPANY, "Company")

        graph.add_edge("p1", "p2", EdgeType.KNOWS)
        graph.add_edge("p2", "p3", EdgeType.KNOWS)
        graph.add_edge("p1", "c1", EdgeType.WORKS_AT)
        graph.add_edge("p2", "c1", EdgeType.WORKS_AT)

        return graph

    def test_calculate_degree_centrality(self, sample_graph):
        """Test degree centrality calculation."""
        analyzer = NetworkAnalyzer(sample_graph)
        scores = analyzer.calculate_degree_centrality()

        assert "p1" in scores
        assert "p2" in scores
        # p2 should have highest centrality (3 connections)
        assert scores["p2"] >= scores["p1"]

    def test_find_key_players(self, sample_graph):
        """Test finding key players."""
        analyzer = NetworkAnalyzer(sample_graph)
        key_players = analyzer.find_key_players(top_n=5)

        assert len(key_players) >= 1
        assert "node_id" in key_players[0]
        assert "centrality" in key_players[0]

    def test_detect_communities(self, sample_graph):
        """Test community detection."""
        analyzer = NetworkAnalyzer(sample_graph)
        communities = analyzer.detect_communities()

        assert len(communities) >= 1
        assert all(isinstance(c, Community) for c in communities)

    def test_get_network_statistics(self, sample_graph):
        """Test getting network statistics."""
        analyzer = NetworkAnalyzer(sample_graph)
        stats = analyzer.get_network_statistics()

        assert stats["node_count"] == 4
        assert stats["edge_count"] == 4  # p1-p2, p2-p3, p1-c1, p2-c1
        assert "density" in stats
        assert "node_types" in stats

    def test_analyze_company_proximity(self, sample_graph):
        """Test company proximity analysis."""
        analyzer = NetworkAnalyzer(sample_graph)

        alert = analyzer.analyze_company_proximity(
            entity_id="p1",
            company_nodes=["c1"],
        )

        # p1 has 2 connections: p2 and c1
        # 1/2 = 0.5 proximity to company
        assert alert is not None
        assert alert.proximity_change >= 0.3


class TestGraphNode:
    """Tests for GraphNode dataclass."""

    def test_node_to_dict(self):
        """Test converting node to dict."""
        node = GraphNode(
            id="test_id",
            type=NodeType.PERSON,
            label="Test Person",
            properties={"key": "value"},
        )

        d = node.to_dict()
        assert d["id"] == "test_id"
        assert d["type"] == "person"
        assert d["label"] == "Test Person"

    def test_node_to_cytoscape(self):
        """Test converting node to Cytoscape format."""
        node = GraphNode(
            id="test_id",
            type=NodeType.PERSON,
            label="Test Person",
        )

        cyto = node.to_cytoscape()
        assert cyto["data"]["id"] == "test_id"
        assert cyto["data"]["label"] == "Test Person"


class TestGraphEdge:
    """Tests for GraphEdge dataclass."""

    def test_edge_to_dict(self):
        """Test converting edge to dict."""
        edge = GraphEdge(
            id="edge_1",
            source="p1",
            target="p2",
            type=EdgeType.KNOWS,
            weight=0.8,
        )

        d = edge.to_dict()
        assert d["source"] == "p1"
        assert d["target"] == "p2"
        assert d["weight"] == 0.8

    def test_edge_to_cytoscape(self):
        """Test converting edge to Cytoscape format."""
        edge = GraphEdge(
            id="edge_1",
            source="p1",
            target="p2",
            type=EdgeType.WORKS_AT,
        )

        cyto = edge.to_cytoscape()
        assert cyto["data"]["source"] == "p1"
        assert cyto["data"]["target"] == "p2"
