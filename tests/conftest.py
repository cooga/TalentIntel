"""Pytest configuration and fixtures."""

import pytest
import asyncio
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

# Configure asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_db_session():
    """Create mock database session for testing."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    return session


@pytest.fixture
def sample_entity_data():
    """Sample entity data for testing."""
    return {
        "name": "Test User",
        "github_username": "testuser",
        "twitter_handle": "testuser",
        "current_company": "Test Corp",
        "current_title": "Software Engineer",
        "priority": 5,
    }


@pytest.fixture
def sample_signal_data():
    """Sample signal data for testing."""
    return {
        "entity_id": "ent_test123",
        "signal_type": "profile_updated",
        "confidence": 0.75,
        "source_platform": "github",
        "description": "Profile was updated",
    }
