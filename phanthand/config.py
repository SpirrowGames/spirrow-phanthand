"""Configuration loader for Phanthand."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import List

import yaml
from pydantic import BaseModel, field_validator


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 7300


class SecurityConfig(BaseModel):
    api_key: str = "change-me-to-a-strong-secret"
    allowed_paths: List[str] = []
    max_file_size_mb: int = 10

    @field_validator("allowed_paths", mode="before")
    @classmethod
    def normalize_paths(cls, v: List[str]) -> List[str]:
        """Normalize paths to use forward slashes and resolve."""
        normalized = []
        for p in v:
            resolved = str(Path(p).resolve())
            normalized.append(resolved)
        return normalized

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


class AppConfig(BaseModel):
    server: ServerConfig = ServerConfig()
    security: SecurityConfig = SecurityConfig()


def _find_config_path() -> Path:
    """Find config.yaml by searching up from CWD or using env var."""
    # 1. Environment variable
    env_path = os.environ.get("PHANTHAND_CONFIG")
    if env_path:
        p = Path(env_path)
        if p.exists():
            return p

    # 2. Current working directory
    cwd = Path.cwd() / "config.yaml"
    if cwd.exists():
        return cwd

    # 3. Same directory as the package
    pkg_dir = Path(__file__).parent.parent / "config.yaml"
    if pkg_dir.exists():
        return pkg_dir

    raise FileNotFoundError(
        "config.yaml not found. Set PHANTHAND_CONFIG env var or run from project root."
    )


@lru_cache(maxsize=1)
def get_config() -> AppConfig:
    """Load and cache application configuration."""
    config_path = _find_config_path()
    with open(config_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raw = {}

    return AppConfig(**raw)
