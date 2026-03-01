"""GitHub data collector for fetching user profiles and events."""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import aiohttp
import structlog

from src.config import get_settings

logger = structlog.get_logger()


class GitHubAPIError(Exception):
    """GitHub API error."""

    def __init__(self, message: str, status_code: int | None = None):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class RateLimitError(GitHubAPIError):
    """GitHub API rate limit exceeded."""

    def __init__(self, reset_time: datetime | None = None):
        self.reset_time = reset_time
        super().__init__("GitHub API rate limit exceeded", status_code=403)


class NotFoundError(GitHubAPIError):
    """GitHub resource not found."""

    def __init__(self, resource: str):
        super().__init__(f"GitHub resource not found: {resource}", status_code=404)


@dataclass
class GitHubProfile:
    """GitHub profile data."""

    username: str
    name: str | None
    bio: str | None
    company: str | None
    location: str | None
    email: str | None
    blog: str | None
    twitter_username: str | None
    public_repos: int
    public_gists: int
    followers: int
    following: int
    created_at: datetime
    updated_at: datetime
    avatar_url: str
    html_url: str
    raw_data: dict[str, Any]


@dataclass
class GitHubEvent:
    """GitHub event data."""

    event_id: str
    event_type: str
    actor: str
    repo: str
    created_at: datetime
    payload: dict[str, Any]
    raw_data: dict[str, Any]


@dataclass
class GitHubChanges:
    """Detected changes in GitHub profile."""

    field: str
    old_value: Any
    new_value: Any
    change_type: str  # 'added', 'removed', 'modified'


class GitHubCollector:
    """GitHub API collector for fetching user data."""

    def __init__(self, token: str | None = None) -> None:
        """Initialize GitHub collector.

        Args:
            token: GitHub personal access token. If not provided, uses settings.
        """
        settings = get_settings()
        self.token = token or settings.github_token
        self.base_url = settings.github_api_base_url
        self.timeout = settings.github_request_timeout
        self.max_retries = settings.github_max_retries
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create HTTP session."""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session

    async def close(self) -> None:
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def _get_headers(self, etag: str | None = None) -> dict[str, str]:
        """Build request headers.

        Args:
            etag: Optional ETag for conditional requests.

        Returns:
            Headers dictionary.
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TalentIntel-Sentinel/0.1.0",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        if etag:
            headers["If-None-Match"] = etag
        return headers

    async def _request(
        self,
        endpoint: str,
        etag: str | None = None,
    ) -> tuple[dict[str, Any] | None, str | None, int]:
        """Make API request to GitHub.

        Args:
            endpoint: API endpoint (e.g., '/users/username').
            etag: Optional ETag for conditional requests.

        Returns:
            Tuple of (response_data, new_etag, status_code).

        Raises:
            GitHubAPIError: On API errors.
            RateLimitError: On rate limit exceeded.
            NotFoundError: On resource not found.
        """
        session = await self._get_session()
        url = f"{self.base_url}{endpoint}"
        headers = self._get_headers(etag)

        logger.debug("github_api_request", url=url, has_etag=etag is not None)

        async with session.get(url, headers=headers) as response:
            status_code = response.status
            new_etag = response.headers.get("ETag")

            # Handle rate limiting
            if status_code == 403:
                rate_remaining = response.headers.get("X-RateLimit-Remaining", "0")
                if rate_remaining == "0":
                    reset_timestamp = response.headers.get("X-RateLimit-Reset")
                    reset_time = None
                    if reset_timestamp:
                        reset_time = datetime.fromtimestamp(int(reset_timestamp))
                    raise RateLimitError(reset_time=reset_time)

            # Handle not found
            if status_code == 404:
                raise NotFoundError(endpoint)

            # Handle not modified (conditional request)
            if status_code == 304:
                logger.debug("github_not_modified", endpoint=endpoint)
                return None, new_etag, status_code

            # Handle other errors
            if status_code >= 400:
                error_data = {}
                try:
                    error_data = await response.json()
                except Exception:
                    pass
                error_msg = error_data.get("message", f"HTTP {status_code}")
                raise GitHubAPIError(error_msg, status_code)

            data = await response.json()
            return data, new_etag, status_code

    async def fetch_profile(
        self,
        username: str,
        etag: str | None = None,
    ) -> tuple[GitHubProfile | None, str | None]:
        """Fetch GitHub user profile.

        Args:
            username: GitHub username.
            etag: Optional ETag for conditional requests.

        Returns:
            Tuple of (profile_data, new_etag). Profile is None if not modified.

        Raises:
            GitHubAPIError: On API errors.
            NotFoundError: If user not found.
        """
        logger.info("fetching_github_profile", username=username)

        try:
            data, new_etag, status_code = await self._request(
                f"/users/{username}", etag=etag
            )

            # Not modified
            if status_code == 304 or data is None:
                return None, new_etag

            profile = GitHubProfile(
                username=data.get("login", username),
                name=data.get("name"),
                bio=data.get("bio"),
                company=data.get("company"),
                location=data.get("location"),
                email=data.get("email"),
                blog=data.get("blog"),
                twitter_username=data.get("twitter_username"),
                public_repos=data.get("public_repos", 0),
                public_gists=data.get("public_gists", 0),
                followers=data.get("followers", 0),
                following=data.get("following", 0),
                created_at=self._parse_github_datetime(data.get("created_at")),
                updated_at=self._parse_github_datetime(data.get("updated_at")),
                avatar_url=data.get("avatar_url", ""),
                html_url=data.get("html_url", ""),
                raw_data=data,
            )

            logger.info(
                "github_profile_fetched",
                username=username,
                repos=profile.public_repos,
                followers=profile.followers,
            )

            return profile, new_etag

        except NotFoundError:
            logger.warning("github_user_not_found", username=username)
            raise

    async def fetch_events(
        self,
        username: str,
        etag: str | None = None,
        per_page: int = 100,
    ) -> tuple[list[GitHubEvent], str | None]:
        """Fetch GitHub user events.

        Args:
            username: GitHub username.
            etag: Optional ETag for conditional requests.
            per_page: Number of events per page (max 100).

        Returns:
            Tuple of (events_list, new_etag).

        Raises:
            GitHubAPIError: On API errors.
            NotFoundError: If user not found.
        """
        logger.info("fetching_github_events", username=username)

        try:
            data, new_etag, status_code = await self._request(
                f"/users/{username}/events?per_page={per_page}", etag=etag
            )

            # Not modified
            if status_code == 304 or data is None:
                return [], new_etag

            events = []
            for event_data in data:
                event = GitHubEvent(
                    event_id=event_data.get("id", ""),
                    event_type=event_data.get("type", ""),
                    actor=event_data.get("actor", {}).get("login", ""),
                    repo=event_data.get("repo", {}).get("name", ""),
                    created_at=self._parse_github_datetime(event_data.get("created_at")),
                    payload=event_data.get("payload", {}),
                    raw_data=event_data,
                )
                events.append(event)

            logger.info(
                "github_events_fetched",
                username=username,
                count=len(events),
            )

            return events, new_etag

        except NotFoundError:
            logger.warning("github_user_not_found", username=username)
            raise

    def detect_changes(
        self,
        current: GitHubProfile,
        previous_snapshot: dict[str, Any] | None,
    ) -> list[GitHubChanges]:
        """Detect changes between current profile and previous snapshot.

        Args:
            current: Current GitHub profile.
            previous_snapshot: Previous snapshot data (raw_data field).

        Returns:
            List of detected changes.
        """
        if previous_snapshot is None:
            return []

        changes: list[GitHubChanges] = []

        # Fields to compare
        compare_fields = [
            ("name", current.name, previous_snapshot.get("name")),
            ("bio", current.bio, previous_snapshot.get("bio")),
            ("company", current.company, previous_snapshot.get("company")),
            ("location", current.location, previous_snapshot.get("location")),
            ("email", current.email, previous_snapshot.get("email")),
            ("blog", current.blog, previous_snapshot.get("blog")),
            ("twitter_username", current.twitter_username, previous_snapshot.get("twitter_username")),
        ]

        for field_name, current_value, previous_value in compare_fields:
            if current_value != previous_value:
                change_type = self._determine_change_type(current_value, previous_value)
                changes.append(GitHubChanges(
                    field=field_name,
                    old_value=previous_value,
                    new_value=current_value,
                    change_type=change_type,
                ))

        # Check numeric fields with thresholds
        numeric_changes = self._detect_numeric_changes(current, previous_snapshot)
        changes.extend(numeric_changes)

        if changes:
            logger.info(
                "github_changes_detected",
                username=current.username,
                changes_count=len(changes),
                fields=[c.field for c in changes],
            )

        return changes

    def _determine_change_type(
        self,
        current_value: Any,
        previous_value: Any,
    ) -> str:
        """Determine the type of change.

        Args:
            current_value: Current value.
            previous_value: Previous value.

        Returns:
            Change type: 'added', 'removed', or 'modified'.
        """
        if previous_value is None and current_value is not None:
            return "added"
        if previous_value is not None and current_value is None:
            return "removed"
        return "modified"

    def _detect_numeric_changes(
        self,
        current: GitHubProfile,
        previous: dict[str, Any],
        threshold_percent: float = 0.2,
    ) -> list[GitHubChanges]:
        """Detect significant changes in numeric fields.

        Args:
            current: Current profile.
            previous: Previous snapshot.
            threshold_percent: Threshold for significant change.

        Returns:
            List of numeric changes.
        """
        changes: list[GitHubChanges] = []

        numeric_fields = [
            ("public_repos", current.public_repos, previous.get("public_repos", 0)),
            ("followers", current.followers, previous.get("followers", 0)),
            ("following", current.following, previous.get("following", 0)),
        ]

        for field_name, current_value, previous_value in numeric_fields:
            if previous_value is None:
                continue

            diff = current_value - previous_value
            if diff == 0:
                continue

            # Calculate percentage change (avoid division by zero)
            if previous_value > 0:
                percent_change = abs(diff / previous_value)
                if percent_change >= threshold_percent:
                    changes.append(GitHubChanges(
                        field=field_name,
                        old_value=previous_value,
                        new_value=current_value,
                        change_type="modified",
                    ))

        return changes

    @staticmethod
    def _parse_github_datetime(date_str: str | None) -> datetime:
        """Parse GitHub datetime string.

        Args:
            date_str: ISO format datetime string.

        Returns:
            Parsed datetime or epoch if invalid.
        """
        if not date_str:
            return datetime(1970, 1, 1)

        # GitHub uses ISO 8601 format
        try:
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            return datetime(1970, 1, 1)

    @staticmethod
    def compute_hash(data: dict[str, Any]) -> str:
        """Compute hash for snapshot data.

        Args:
            data: Snapshot data dictionary.

        Returns:
            SHA256 hash string.
        """
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
