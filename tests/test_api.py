"""Integration tests for API endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient


class TestHealthEndpoint:
    """Tests for GET /health (no auth required)."""

    def test_health_ok(self, client: TestClient):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["status"] == "ok"
        assert "version" in body["data"]
        assert "hostname" in body["data"]
        assert body["data"]["uptime_seconds"] >= 0


class TestAuthentication:
    """Tests for Bearer token authentication."""

    def test_no_auth_header(self, client: TestClient, tmp_workspace: Path):
        resp = client.post("/files/exists", json={"path": str(tmp_workspace / "hello.txt")})
        assert resp.status_code in (401, 403)  # No credentials

    def test_wrong_api_key(self, client: TestClient, tmp_workspace: Path):
        resp = client.post(
            "/files/exists",
            json={"path": str(tmp_workspace / "hello.txt")},
            headers={"Authorization": "Bearer wrong-key"},
        )
        assert resp.status_code == 401

    def test_valid_api_key(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/exists",
            json={"path": str(tmp_workspace / "hello.txt")},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True


class TestFileReadEndpoint:
    """Tests for POST /files/read."""

    def test_read_success(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/read",
            json={"path": str(tmp_workspace / "hello.txt")},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["content"] == "Hello, World!"

    def test_read_not_found(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/read",
            json={"path": str(tmp_workspace / "missing.txt")},
            headers=auth_headers,
        )
        body = resp.json()
        assert body["success"] is False
        assert "not found" in body["error"].lower()

    def test_read_disallowed_path(self, client: TestClient, auth_headers: dict):
        resp = client.post(
            "/files/read",
            json={"path": "C:/Windows/System32/config/SAM"},
            headers=auth_headers,
        )
        body = resp.json()
        assert body["success"] is False
        assert "not allowed" in body["error"].lower()


class TestFileListEndpoint:
    """Tests for POST /files/list."""

    def test_list_success(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/list",
            json={"path": str(tmp_workspace)},
            headers=auth_headers,
        )
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["count"] > 0
        names = [e["name"] for e in body["data"]["entries"]]
        assert "hello.txt" in names

    def test_list_with_pattern(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/list",
            json={"path": str(tmp_workspace), "pattern": "*.json"},
            headers=auth_headers,
        )
        body = resp.json()
        assert body["success"] is True
        names = [e["name"] for e in body["data"]["entries"]]
        assert "data.json" in names
        assert "hello.txt" not in names


class TestFileExistsEndpoint:
    """Tests for POST /files/exists."""

    def test_exists_true(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/exists",
            json={"path": str(tmp_workspace / "hello.txt")},
            headers=auth_headers,
        )
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["exists"] is True
        assert body["data"]["is_file"] is True

    def test_exists_false(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/exists",
            json={"path": str(tmp_workspace / "nope.txt")},
            headers=auth_headers,
        )
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["exists"] is False


class TestFileInfoEndpoint:
    """Tests for POST /files/info."""

    def test_info_success(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/info",
            json={"path": str(tmp_workspace / "hello.txt")},
            headers=auth_headers,
        )
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["name"] == "hello.txt"
        assert body["data"]["size"] == 13


class TestFileTreeEndpoint:
    """Tests for POST /files/tree."""

    def test_tree_success(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/tree",
            json={"path": str(tmp_workspace), "max_depth": 2},
            headers=auth_headers,
        )
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["tree"]["is_dir"] is True
        assert len(body["data"]["tree"]["children"]) > 0


class TestFileSearchEndpoint:
    """Tests for POST /files/search."""

    def test_search_success(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/search",
            json={"path": str(tmp_workspace), "pattern": "*.txt"},
            headers=auth_headers,
        )
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["count"] >= 1

    def test_search_no_match(self, client: TestClient, tmp_workspace: Path, auth_headers: dict):
        resp = client.post(
            "/files/search",
            json={"path": str(tmp_workspace), "pattern": "*.zzz"},
            headers=auth_headers,
        )
        body = resp.json()
        assert body["success"] is True
        assert body["data"]["count"] == 0
