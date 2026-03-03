"""Entity management API routes."""

from datetime import datetime
from typing import Any, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_session
from src.models.entity import Entity, EntityCreate, EntityUpdate, EntityResponse, CareerState
from src.sentinel.entity_service import EntityService

router = APIRouter()


class EntityListResponse(BaseModel):
    """Response for entity list."""
    entities: list[EntityResponse]
    total: int
    page: int
    page_size: int


class EntityCreateRequest(BaseModel):
    """Request for creating entity."""
    name: str = Field(..., min_length=1, max_length=255)
    github_username: str | None = Field(None, max_length=255)
    twitter_handle: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=512)
    personal_website: str | None = Field(None, max_length=512)
    current_company: str | None = Field(None, max_length=255)
    current_title: str | None = Field(None, max_length=255)
    priority: int = Field(default=5, ge=1, le=10)
    tags: list[str] | None = None
    notes: str | None = None


class EntityUpdateRequest(BaseModel):
    """Request for updating entity."""
    name: str | None = Field(None, min_length=1, max_length=255)
    github_username: str | None = Field(None, max_length=255)
    twitter_handle: str | None = Field(None, max_length=255)
    linkedin_url: str | None = Field(None, max_length=512)
    personal_website: str | None = Field(None, max_length=512)
    current_company: str | None = Field(None, max_length=255)
    current_title: str | None = Field(None, max_length=255)
    priority: int | None = Field(None, ge=1, le=10)
    tags: list[str] | None = None
    notes: str | None = None
    is_active: bool | None = None


@router.get("/", response_model=EntityListResponse)
async def list_entities(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: bool | None = None,
    state: str | None = None,
    min_priority: int | None = None,
    session: AsyncSession = Depends(get_session),
) -> EntityListResponse:
    """List all entities with optional filters."""
    service = EntityService(session)

    query = select(Entity)

    if is_active is not None:
        query = query.where(Entity.is_active == is_active)
    if state:
        query = query.where(Entity.current_state == state)
    if min_priority:
        query = query.where(Entity.priority >= min_priority)

    # Count total
    count_query = select(Entity)
    if is_active is not None:
        count_query = count_query.where(Entity.is_active == is_active)
    if state:
        count_query = count_query.where(Entity.current_state == state)
    if min_priority:
        count_query = count_query.where(Entity.priority >= min_priority)

    result = await session.execute(count_query)
    total = len(list(result.scalars().all()))

    # Paginate
    query = query.offset((page - 1) * page_size).limit(page_size)
    query = query.order_by(Entity.priority.desc())

    result = await session.execute(query)
    entities = list(result.scalars().all())

    return EntityListResponse(
        entities=[EntityResponse.model_validate(e) for e in entities],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: str,
    session: AsyncSession = Depends(get_session),
) -> EntityResponse:
    """Get a specific entity."""
    service = EntityService(session)
    entity = await service.get_entity(entity_id)

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    return EntityResponse.model_validate(entity)


@router.post("/", response_model=EntityResponse, status_code=201)
async def create_entity(
    request: EntityCreateRequest,
    session: AsyncSession = Depends(get_session),
) -> EntityResponse:
    """Create a new entity."""
    service = EntityService(session)

    entity = await service.create_entity(EntityCreate(**request.model_dump()))
    await session.commit()

    return EntityResponse.model_validate(entity)


@router.put("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: str,
    request: EntityUpdateRequest,
    session: AsyncSession = Depends(get_session),
) -> EntityResponse:
    """Update an entity."""
    service = EntityService(session)

    update_data = {k: v for k, v in request.model_dump().items() if v is not None}
    entity = await service.update_entity(entity_id, EntityUpdate(**update_data))

    if not entity:
        raise HTTPException(status_code=404, detail="Entity not found")

    await session.commit()
    return EntityResponse.model_validate(entity)


@router.delete("/{entity_id}", status_code=204)
async def delete_entity(
    entity_id: str,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Delete an entity."""
    service = EntityService(session)
    success = await service.delete_entity(entity_id)

    if not success:
        raise HTTPException(status_code=404, detail="Entity not found")

    await session.commit()


@router.get("/{entity_id}/state", response_model=dict[str, Any])
async def get_entity_state(
    entity_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Get entity state information."""
    from src.sentinel.state_machine import StateInferenceEngine

    engine = StateInferenceEngine(session)
    summary = await engine.get_state_summary(entity_id)

    if "error" in summary:
        raise HTTPException(status_code=404, detail=summary["error"])

    return summary
