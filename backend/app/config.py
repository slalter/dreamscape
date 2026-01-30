"""Application configuration with environment variable overrides."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Literal


@dataclass
class LLMConfig:
    """Configuration for the LLM service."""

    provider: Literal["openai"] = "openai"
    model: str = "gpt-4o"
    max_tokens: int = 4096
    temperature: float = 0.7
    api_key: str = field(default_factory=lambda: os.environ.get("OPENAI_API_KEY", ""))

    def __post_init__(self) -> None:
        if not self.api_key:
            self.api_key = os.environ.get("OPENAI_API_KEY", "")


@dataclass
class WorldConfig:
    """Configuration for world/scene parameters."""

    max_objects: int = 200
    max_terrain_segments: int = 50
    default_gravity: float = -9.81
    world_bounds: float = 500.0  # half-extent in each direction
    generation_timeout_seconds: float = 30.0


@dataclass
class ServerConfig:
    """Configuration for the FastAPI server."""

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = field(default_factory=lambda: ["http://localhost:3000", "http://localhost:5173"])
    websocket_ping_interval: float = 30.0
    websocket_ping_timeout: float = 10.0


@dataclass
class AppConfig:
    """Top-level application configuration."""

    llm: LLMConfig = field(default_factory=LLMConfig)
    world: WorldConfig = field(default_factory=WorldConfig)
    server: ServerConfig = field(default_factory=ServerConfig)
    debug: bool = field(default_factory=lambda: os.environ.get("DEBUG", "false").lower() == "true")
    log_level: str = field(default_factory=lambda: os.environ.get("LOG_LEVEL", "INFO"))

    @classmethod
    def from_env(cls) -> AppConfig:
        """Create config from environment variables."""
        return cls(
            llm=LLMConfig(
                model=os.environ.get("LLM_MODEL", "gpt-4o"),
                max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "4096")),
                temperature=float(os.environ.get("LLM_TEMPERATURE", "0.7")),
            ),
            world=WorldConfig(
                max_objects=int(os.environ.get("MAX_OBJECTS", "200")),
                generation_timeout_seconds=float(os.environ.get("GENERATION_TIMEOUT", "30.0")),
            ),
            server=ServerConfig(
                host=os.environ.get("HOST", "0.0.0.0"),
                port=int(os.environ.get("PORT", "8000")),
            ),
        )


# Global config instance
config = AppConfig.from_env()
