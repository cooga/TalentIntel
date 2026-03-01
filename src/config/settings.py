"""Application settings and configuration management."""

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_prefix="SENTINEL_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database settings
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/sentinel.db",
        description="Database connection URL (async supported)",
    )
    database_echo: bool = Field(
        default=False,
        description="Enable SQLAlchemy query logging",
    )

    # GitHub API settings
    github_token: str | None = Field(
        default=None,
        description="GitHub personal access token for API authentication",
    )
    github_api_base_url: str = Field(
        default="https://api.github.com",
        description="GitHub API base URL",
    )
    github_request_timeout: int = Field(
        default=30,
        description="GitHub API request timeout in seconds",
    )
    github_max_retries: int = Field(
        default=3,
        description="Maximum retries for GitHub API requests",
    )

    # Monitoring settings
    default_check_interval: int = Field(
        default=3600,  # 1 hour
        description="Default interval between checks in seconds",
    )
    baseline_learning_period: int = Field(
        default=14,  # 14 days
        description="Baseline learning period in days",
    )

    # Logging settings
    log_level: str = Field(
        default="INFO",
        description="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or console)",
    )

    # Alert settings
    alert_discord_webhook: str | None = Field(
        default=None,
        description="Discord webhook URL for alerts",
    )
    alert_min_confidence: float = Field(
        default=0.7,
        description="Minimum confidence threshold for alerts",
    )

    # Application settings
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    data_dir: Path = Field(
        default=Path("./data"),
        description="Data directory path",
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid_levels}")
        return v_upper

    @field_validator("data_dir")
    @classmethod
    def validate_data_dir(cls, v: Path) -> Path:
        """Ensure data directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @classmethod
    def from_yaml(cls, config_path: Path) -> "Settings":
        """Load settings from YAML file.

        Environment variables take precedence over YAML values.

        Args:
            config_path: Path to YAML configuration file.

        Returns:
            Settings instance with merged configuration.
        """
        if not config_path.exists():
            return cls()

        with open(config_path) as f:
            config_data = yaml.safe_load(f) or {}

        # Flatten nested config for pydantic
        flat_config: dict[str, Any] = {}
        for key, value in config_data.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat_config[f"{key}_{sub_key}"] = sub_value
            else:
                flat_config[key] = value

        return cls(**flat_config)


@lru_cache
def get_settings(config_path: Path | None = None) -> Settings:
    """Get cached settings instance.

    Args:
        config_path: Optional path to YAML configuration file.

    Returns:
        Cached Settings instance.
    """
    if config_path:
        return Settings.from_yaml(config_path)

    # Try default config locations
    default_paths = [
        Path("config/config.yaml"),
        Path("config/config.yml"),
        Path("sentinel.yaml"),
        Path("sentinel.yml"),
    ]

    for path in default_paths:
        if path.exists():
            return Settings.from_yaml(path)

    return Settings()
