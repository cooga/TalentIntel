"""FastAPI routes for TalentIntel API."""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Any

from src.api.entities import router as entities_router
from src.api.analysis import router as analysis_router
from src.api.network import router as network_router

api_router = APIRouter()

# Include all sub-routers
api_router.include_router(entities_router, prefix="/entities", tags=["entities"])
api_router.include_router(analysis_router, prefix="/analysis", tags=["analysis"])
api_router.include_router(network_router, prefix="/network", tags=["network"])


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str


@api_router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check API health."""
    return HealthResponse(status="healthy", version="1.0.0")
