"""Network graph API routes for relationship visualization."""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.models.entity import Entity
from src.graph.relationship_graph import RelationshipGraph, NodeType, EdgeType
from src.graph.network_analyzer import NetworkAnalyzer

router = APIRouter()


class GraphNodeData(BaseModel):
    """Node data for visualization."""
    id: str
    label: str
    type: str
    group: str = "default"
    size: float = 1.0


class GraphEdgeData(BaseModel):
    """Edge data for visualization."""
    id: str
    source: str
    target: str
    type: str
    weight: float = 1.0


class GraphDataResponse(BaseModel):
    """Response for graph data."""
    nodes: list[GraphNodeData]
    edges: list[GraphEdgeData]
    metadata: dict[str, Any]


class NetworkStatsResponse(BaseModel):
    """Response for network statistics."""
    node_count: int
    edge_count: int
    density: float
    node_types: dict[str, int]
    edge_types: dict[str, int]
    avg_centrality: float | None
    community_count: int | None


class KeyPlayerResponse(BaseModel):
    """Response for key player."""
    node_id: str
    label: str
    centrality: float
    connections: int


class PathResponse(BaseModel):
    """Response for path finding."""
    source: str
    target: str
    path: list[str]
    length: int


async def build_graph_from_entities(session: AsyncSession) -> RelationshipGraph:
    """Build relationship graph from entities."""
    graph = RelationshipGraph()

    # Get all entities
    query = select(Entity).where(Entity.is_active == True)
    result = await session.execute(query)
    entities = list(result.scalars().all())

    # Add person nodes
    for entity in entities:
        graph.add_node(
            node_id=entity.id,
            node_type=NodeType.PERSON,
            label=entity.name,
            properties={
                "company": entity.current_company,
                "title": entity.current_title,
                "state": entity.current_state,
                "priority": entity.priority,
            },
        )

        # Add company node and edge
        if entity.current_company:
            company_id = f"company:{entity.current_company.lower().replace(' ', '_')}"
            graph.add_node(
                node_id=company_id,
                node_type=NodeType.COMPANY,
                label=entity.current_company,
            )
            graph.add_edge(
                source_id=entity.id,
                target_id=company_id,
                edge_type=EdgeType.WORKS_AT,
                weight=1.0,
            )

    return graph


@router.get("/", response_model=GraphDataResponse)
async def get_network_graph(
    depth: int = Query(2, ge=1, le=4),
    session: AsyncSession = Depends(get_session),
) -> GraphDataResponse:
    """Get full network graph for visualization."""
    graph = await build_graph_from_entities(session)

    # Convert to visualization format
    nodes = [
        GraphNodeData(
            id=node.id,
            label=node.label,
            type=node.type.value,
            group=node.type.value,
            size=1.0 + len(graph.get_neighbors(node.id)) * 0.1,
        )
        for node in graph.nodes.values()
    ]

    edges = [
        GraphEdgeData(
            id=edge.id,
            source=edge.source,
            target=edge.target,
            type=edge.type.value,
            weight=edge.weight,
        )
        for edge in graph.edges.values()
    ]

    return GraphDataResponse(
        nodes=nodes,
        edges=edges,
        metadata={
            "node_count": len(nodes),
            "edge_count": len(edges),
        },
    )


@router.get("/entity/{entity_id}", response_model=GraphDataResponse)
async def get_entity_network(
    entity_id: str,
    depth: int = Query(2, ge=1, le=4),
    session: AsyncSession = Depends(get_session),
) -> GraphDataResponse:
    """Get network graph centered on an entity."""
    graph = await build_graph_from_entities(session)

    # Get subgraph
    nodes, edges = graph.get_subgraph(entity_id, depth)

    if not nodes:
        raise HTTPException(status_code=404, detail="Entity not found in graph")

    node_data = [
        GraphNodeData(
            id=node.id,
            label=node.label,
            type=node.type.value,
            group=node.type.value,
            size=1.0 + len(graph.get_neighbors(node.id)) * 0.1,
        )
        for node in nodes
    ]

    edge_data = [
        GraphEdgeData(
            id=edge.id,
            source=edge.source,
            target=edge.target,
            type=edge.type.value,
            weight=edge.weight,
        )
        for edge in edges
    ]

    return GraphDataResponse(
        nodes=node_data,
        edges=edge_data,
        metadata={
            "center_entity": entity_id,
            "depth": depth,
            "node_count": len(node_data),
            "edge_count": len(edge_data),
        },
    )


@router.get("/stats", response_model=NetworkStatsResponse)
async def get_network_stats(
    session: AsyncSession = Depends(get_session),
) -> NetworkStatsResponse:
    """Get network statistics."""
    graph = await build_graph_from_entities(session)
    analyzer = NetworkAnalyzer(graph)
    stats = analyzer.get_network_statistics()

    return NetworkStatsResponse(
        node_count=stats.get("node_count", 0),
        edge_count=stats.get("edge_count", 0),
        density=stats.get("density", 0.0),
        node_types=stats.get("node_types", {}),
        edge_types=stats.get("edge_types", {}),
        avg_centrality=stats.get("avg_centrality"),
        community_count=stats.get("community_count"),
    )


@router.get("/key-players", response_model=list[KeyPlayerResponse])
async def get_key_players(
    top_n: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> list[KeyPlayerResponse]:
    """Get key players in the network."""
    graph = await build_graph_from_entities(session)
    analyzer = NetworkAnalyzer(graph)
    key_players = analyzer.find_key_players(top_n)

    return [
        KeyPlayerResponse(
            node_id=player["node_id"],
            label=player["label"],
            centrality=player["centrality"],
            connections=player["connections"],
        )
        for player in key_players
    ]


@router.get("/path", response_model=PathResponse | None)
async def find_path(
    source_id: str = Query(...),
    target_id: str = Query(...),
    max_depth: int = Query(4, ge=1, le=6),
    session: AsyncSession = Depends(get_session),
) -> PathResponse | None:
    """Find path between two entities."""
    graph = await build_graph_from_entities(session)
    path = graph.find_path(source_id, target_id, max_depth)

    if not path:
        return None

    # Get labels for path
    labels = []
    for node_id in path:
        node = graph.get_node(node_id)
        labels.append(node.label if node else node_id)

    return PathResponse(
        source=source_id,
        target=target_id,
        path=labels,
        length=len(path) - 1,
    )


@router.get("/communities", response_model=list[dict[str, Any]])
async def get_communities(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    """Detect communities in the network."""
    graph = await build_graph_from_entities(session)
    analyzer = NetworkAnalyzer(graph)
    communities = analyzer.detect_communities()

    return [
        {
            "community_id": c.community_id,
            "size": c.size,
            "density": c.density,
            "members": [
                {"id": nid, "label": graph.get_node(nid).label if graph.get_node(nid) else nid}
                for nid in c.nodes[:10]  # Limit members shown
            ],
        }
        for c in communities[:20]  # Limit communities
    ]
