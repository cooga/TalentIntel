"""Analysis API routes for key person intelligence."""

from typing import Any
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.analysis.key_person_analyzer import KeyPersonAnalyzer
from src.analysis.decision_engine import DecisionEngine, Priority

router = APIRouter()


class PersonIntelligenceResponse(BaseModel):
    """Response for person intelligence."""
    entity_id: str
    name: str
    current_state: str
    state_confidence: float
    current_company: str | None
    current_title: str | None
    departure_risk: float
    risk_factors: list[str]
    signal_summary: dict[str, int]
    network_centrality: float
    key_connections: list[str]
    predicted_next_state: str | None
    prediction_confidence: float


class RecommendationResponse(BaseModel):
    """Response for a recommendation."""
    entity_id: str
    entity_name: str
    type: str
    priority: str
    confidence: float
    reason: str
    actions: list[str]


class DecisionReportResponse(BaseModel):
    """Response for decision report."""
    generated_at: str
    summary: dict[str, Any]
    state_distribution: dict[str, int]
    recommendations_by_priority: dict[str, int]
    top_recommendations: list[RecommendationResponse]


@router.get("/{entity_id}", response_model=PersonIntelligenceResponse)
async def analyze_person(
    entity_id: str,
    session: AsyncSession = Depends(get_session),
) -> PersonIntelligenceResponse:
    """Get comprehensive intelligence analysis for a person."""
    analyzer = KeyPersonAnalyzer(session)
    intel = await analyzer.analyze_person(entity_id)

    if not intel:
        raise HTTPException(status_code=404, detail="Entity not found")

    return PersonIntelligenceResponse(
        entity_id=intel.entity_id,
        name=intel.name,
        current_state=intel.current_state.value,
        state_confidence=intel.state_confidence,
        current_company=intel.current_company,
        current_title=intel.current_title,
        departure_risk=intel.departure_risk,
        risk_factors=intel.risk_factors,
        signal_summary=intel.signal_summary,
        network_centrality=intel.network_centrality,
        key_connections=intel.key_connections,
        predicted_next_state=intel.predicted_next_state.value if intel.predicted_next_state else None,
        prediction_confidence=intel.prediction_confidence,
    )


@router.get("/high-risk", response_model=list[PersonIntelligenceResponse])
async def get_high_risk_persons(
    threshold: float = Query(0.6, ge=0, le=1),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> list[PersonIntelligenceResponse]:
    """Get persons with high departure risk."""
    analyzer = KeyPersonAnalyzer(session)
    high_risk = await analyzer.get_high_risk_persons(threshold, limit)

    return [
        PersonIntelligenceResponse(
            entity_id=i.entity_id,
            name=i.name,
            current_state=i.current_state.value,
            state_confidence=i.state_confidence,
            current_company=i.current_company,
            current_title=i.current_title,
            departure_risk=i.departure_risk,
            risk_factors=i.risk_factors,
            signal_summary=i.signal_summary,
            network_centrality=i.network_centrality,
            key_connections=i.key_connections,
            predicted_next_state=i.predicted_next_state.value if i.predicted_next_state else None,
            prediction_confidence=i.prediction_confidence,
        )
        for i in high_risk
    ]


@router.get("/attention", response_model=list[PersonIntelligenceResponse])
async def get_attention_needed(
    limit: int = Query(10, ge=1, le=50),
    session: AsyncSession = Depends(get_session),
) -> list[PersonIntelligenceResponse]:
    """Get persons that need immediate attention."""
    analyzer = KeyPersonAnalyzer(session)
    persons = await analyzer.get_attention_needed(limit)

    return [
        PersonIntelligenceResponse(
            entity_id=i.entity_id,
            name=i.name,
            current_state=i.current_state.value,
            state_confidence=i.state_confidence,
            current_company=i.current_company,
            current_title=i.current_title,
            departure_risk=i.departure_risk,
            risk_factors=i.risk_factors,
            signal_summary=i.signal_summary,
            network_centrality=i.network_centrality,
            key_connections=i.key_connections,
            predicted_next_state=i.predicted_next_state.value if i.predicted_next_state else None,
            prediction_confidence=i.prediction_confidence,
        )
        for i in persons
    ]


@router.get("/recommendations", response_model=DecisionReportResponse)
async def get_recommendations(
    min_priority: int = Query(5, ge=1, le=10),
    session: AsyncSession = Depends(get_session),
) -> DecisionReportResponse:
    """Get decision recommendations."""
    engine = DecisionEngine(session)
    report = await engine.generate_recommendations(min_priority=min_priority)

    return DecisionReportResponse(
        generated_at=report.generated_at.isoformat(),
        summary={
            "total_analyzed": report.total_analyzed,
            "high_priority_count": report.high_priority_count,
            "average_risk": report.average_risk,
        },
        state_distribution=report.state_distribution,
        recommendations_by_priority={
            p.value: sum(1 for r in report.recommendations if r.priority == p)
            for p in Priority
        },
        top_recommendations=[
            RecommendationResponse(
                entity_id=r.entity_id,
                entity_name=r.entity_name,
                type=r.type.value,
                priority=r.priority.value,
                confidence=r.confidence,
                reason=r.reason,
                actions=r.actions,
            )
            for r in report.recommendations[:20]
        ],
    )


@router.get("/dashboard", response_model=dict[str, Any])
async def get_dashboard(
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get dashboard data for decision support."""
    engine = DecisionEngine(session)
    return await engine.generate_dashboard_data()


@router.get("/state-distribution", response_model=dict[str, int])
async def get_state_distribution(
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    """Get distribution of career states."""
    analyzer = KeyPersonAnalyzer(session)
    return await analyzer.get_state_distribution()
