"""Entity service layer for managing monitored entities."""

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import generate_id
from src.models.entity import (
    CareerState,
    Entity,
    EntityCreate,
    EntityResponse,
    EntityUpdate,
)

logger = structlog.get_logger()


class EntityNotFoundError(Exception):
    """Entity not found error."""

    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        super().__init__(f"Entity not found: {entity_id}")


class DuplicateEntityError(Exception):
    """Duplicate entity error."""

    def __init__(self, field: str, value: str):
        self.field = field
        self.value = value
        super().__init__(f"Entity with {field}={value} already exists")


class EntityService:
    """Service layer for entity operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize entity service.

        Args:
            session: Database session.
        """
        self.session = session

    async def create_entity(self, entity_create: EntityCreate) -> Entity:
        """Create a new entity.

        Args:
            entity_create: Entity creation data.

        Returns:
            Created entity.

        Raises:
            DuplicateEntityError: If entity with same GitHub username exists.
        """
        logger.info(
            "creating_entity",
            name=entity_create.name,
            github_username=entity_create.github_username,
        )

        # Check for duplicate GitHub username
        if entity_create.github_username:
            existing = await self._find_by_github_username(entity_create.github_username)
            if existing:
                raise DuplicateEntityError("github_username", entity_create.github_username)

        # Create entity
        entity = Entity(
            id=generate_id("ent"),
            name=entity_create.name,
            github_username=entity_create.github_username,
            twitter_handle=entity_create.twitter_handle,
            linkedin_url=entity_create.linkedin_url,
            personal_website=entity_create.personal_website,
            current_company=entity_create.current_company,
            current_title=entity_create.current_title,
            priority=entity_create.priority,
            tags=entity_create.tags,
            notes=entity_create.notes,
            is_active=True,
            current_state=CareerState.UNKNOWN.value,
        )

        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)

        logger.info(
            "entity_created",
            entity_id=entity.id,
            name=entity.name,
        )

        return entity

    async def get_entity(self, entity_id: str) -> Entity | None:
        """Get entity by ID.

        Args:
            entity_id: Entity ID.

        Returns:
            Entity if found, None otherwise.
        """
        result = await self.session.execute(
            select(Entity).where(Entity.id == entity_id)
        )
        return result.scalar_one_or_none()

    async def get_entity_or_raise(self, entity_id: str) -> Entity:
        """Get entity by ID or raise error.

        Args:
            entity_id: Entity ID.

        Returns:
            Entity.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        entity = await self.get_entity(entity_id)
        if entity is None:
            raise EntityNotFoundError(entity_id)
        return entity

    async def list_entities(
        self,
        active_only: bool = False,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Entity]:
        """List all entities.

        Args:
            active_only: Only return active entities.
            limit: Maximum number of entities to return.
            offset: Offset for pagination.

        Returns:
            List of entities.
        """
        query = select(Entity).order_by(Entity.priority.desc(), Entity.created_at.desc())

        if active_only:
            query = query.where(Entity.is_active == True)

        if offset > 0:
            query = query.offset(offset)

        if limit is not None:
            query = query.limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_entity(
        self,
        entity_id: str,
        entity_update: EntityUpdate,
    ) -> Entity:
        """Update an entity.

        Args:
            entity_id: Entity ID.
            entity_update: Entity update data.

        Returns:
            Updated entity.

        Raises:
            EntityNotFoundError: If entity not found.
            DuplicateEntityError: If duplicate GitHub username.
        """
        entity = await self.get_entity_or_raise(entity_id)

        logger.info(
            "updating_entity",
            entity_id=entity_id,
            fields=entity_update.model_dump(exclude_unset=True),
        )

        # Check for duplicate GitHub username if changing
        if entity_update.github_username and entity_update.github_username != entity.github_username:
            existing = await self._find_by_github_username(entity_update.github_username)
            if existing and existing.id != entity_id:
                raise DuplicateEntityError("github_username", entity_update.github_username)

        # Update fields
        update_data = entity_update.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "current_state" and value is not None:
                # Handle CareerState enum
                setattr(entity, field, value.value if isinstance(value, CareerState) else value)
            else:
                setattr(entity, field, value)

        await self.session.flush()
        await self.session.refresh(entity)

        logger.info("entity_updated", entity_id=entity_id)

        return entity

    async def delete_entity(self, entity_id: str) -> bool:
        """Delete an entity.

        Args:
            entity_id: Entity ID.

        Returns:
            True if deleted.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        entity = await self.get_entity_or_raise(entity_id)

        logger.info("deleting_entity", entity_id=entity_id)

        await self.session.delete(entity)
        await self.session.flush()

        logger.info("entity_deleted", entity_id=entity_id)

        return True

    async def set_entity_active(
        self,
        entity_id: str,
        is_active: bool,
    ) -> Entity:
        """Set entity active status.

        Args:
            entity_id: Entity ID.
            is_active: Active status.

        Returns:
            Updated entity.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        entity = await self.get_entity_or_raise(entity_id)
        entity.is_active = is_active

        await self.session.flush()
        await self.session.refresh(entity)

        logger.info(
            "entity_active_status_changed",
            entity_id=entity_id,
            is_active=is_active,
        )

        return entity

    async def update_entity_state(
        self,
        entity_id: str,
        state: CareerState,
        confidence: float | None = None,
    ) -> Entity:
        """Update entity career state.

        Args:
            entity_id: Entity ID.
            state: New career state.
            confidence: State confidence (0-1).

        Returns:
            Updated entity.

        Raises:
            EntityNotFoundError: If entity not found.
        """
        entity = await self.get_entity_or_raise(entity_id)

        entity.current_state = state.value
        if confidence is not None:
            entity.state_confidence = min(1.0, max(0.0, confidence))

        await self.session.flush()
        await self.session.refresh(entity)

        logger.info(
            "entity_state_updated",
            entity_id=entity_id,
            state=state.value,
            confidence=confidence,
        )

        return entity

    async def find_by_github_username(self, username: str) -> Entity | None:
        """Find entity by GitHub username.

        Args:
            username: GitHub username.

        Returns:
            Entity if found, None otherwise.
        """
        return await self._find_by_github_username(username)

    async def _find_by_github_username(self, username: str) -> Entity | None:
        """Internal method to find entity by GitHub username.

        Args:
            username: GitHub username.

        Returns:
            Entity if found, None otherwise.
        """
        result = await self.session.execute(
            select(Entity).where(Entity.github_username == username)
        )
        return result.scalar_one_or_none()

    @staticmethod
    def entity_to_response(entity: Entity) -> EntityResponse:
        """Convert entity to response model.

        Args:
            entity: Entity instance.

        Returns:
            EntityResponse model.
        """
        return EntityResponse(
            id=entity.id,
            name=entity.name,
            github_username=entity.github_username,
            twitter_handle=entity.twitter_handle,
            linkedin_url=entity.linkedin_url,
            personal_website=entity.personal_website,
            current_state=entity.current_state,
            state_confidence=entity.state_confidence,
            current_company=entity.current_company,
            current_title=entity.current_title,
            is_active=entity.is_active,
            priority=entity.priority,
            tags=entity.tags,
            notes=entity.notes,
            created_at=entity.created_at,
            updated_at=entity.updated_at,
        )
