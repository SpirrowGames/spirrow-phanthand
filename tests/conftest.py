"""Shared test fixtures for Phanthand tests."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def tmp_workspace() -> Generator[Path, None, None]:
    """Create a temporary directory structure for testing."""
    with tempfile.TemporaryDirectory(prefix="phanthand_test_") as tmpdir:
        root = Path(tmpdir)

        # Create test files
        (root / "hello.txt").write_text("Hello, World!", encoding="utf-8")
        (root / "data.json").write_text('{"key": "value"}', encoding="utf-8")
        (root / "empty.txt").write_text("", encoding="utf-8")

        # Create subdirectory
        sub = root / "subdir"
        sub.mkdir()
        (sub / "nested.txt").write_text("nested content", encoding="utf-8")
        (sub / "code.py").write_text("print('hello')", encoding="utf-8")

        # Create deep structure
        deep = sub / "deep"
        deep.mkdir()
        (deep / "deep_file.txt").write_text("deep content", encoding="utf-8")

        yield root


@pytest.fixture(scope="session")
def test_config_path(tmp_workspace: Path) -> Generator[Path, None, None]:
    """Create a temporary config.yaml pointing to the test workspace."""
    import yaml

    config = {
        "server": {"host": "127.0.0.1", "port": 7399},
        "security": {
            "api_key": "test-api-key-12345",
            "allowed_paths": [str(tmp_workspace)],
            "max_file_size_mb": 1,
        },
    }

    config_file = tmp_workspace / "config.yaml"
    with open(config_file, "w", encoding="utf-8") as f:
        yaml.dump(config, f)

    # Set env var and clear config cache
    old_env = os.environ.get("PHANTHAND_CONFIG")
    os.environ["PHANTHAND_CONFIG"] = str(config_file)

    from phanthand.config import get_config
    get_config.cache_clear()

    yield config_file

    # Cleanup
    get_config.cache_clear()
    if old_env is None:
        os.environ.pop("PHANTHAND_CONFIG", None)
    else:
        os.environ["PHANTHAND_CONFIG"] = old_env


@pytest.fixture(scope="session")
def api_key() -> str:
    """Return the test API key."""
    return "test-api-key-12345"


@pytest.fixture(scope="session")
def auth_headers(api_key: str) -> dict:
    """Return auth headers for API requests."""
    return {"Authorization": f"Bearer {api_key}"}


@pytest.fixture(scope="session")
def client(test_config_path: Path) -> Generator[TestClient, None, None]:
    """Create a FastAPI TestClient with test configuration."""
    from phanthand.main import app

    with TestClient(app) as c:
        yield c
