"""Unit tests for FileService."""

from __future__ import annotations

from pathlib import Path

import pytest

from phanthand.services.file_service import FileService, PathNotAllowedError


@pytest.fixture
def service(test_config_path) -> FileService:
    """FileService instance with test config loaded."""
    return FileService()


class TestValidatePath:
    """Tests for path validation and whitelist enforcement."""

    def test_allowed_path(self, service: FileService, tmp_workspace: Path):
        result = service.validate_path(str(tmp_workspace / "hello.txt"))
        assert result == (tmp_workspace / "hello.txt").resolve()

    def test_disallowed_path(self, service: FileService):
        with pytest.raises(PathNotAllowedError):
            service.validate_path("C:/Windows/System32/config")

    def test_parent_traversal_blocked(self, service: FileService, tmp_workspace: Path):
        """Path traversal via .. should be caught after resolution."""
        evil_path = str(tmp_workspace / "subdir" / ".." / ".." / "etc" / "passwd")
        with pytest.raises(PathNotAllowedError):
            service.validate_path(evil_path)


class TestReadFile:
    """Tests for file reading."""

    def test_read_existing_file(self, service: FileService, tmp_workspace: Path):
        result = service.read_file(str(tmp_workspace / "hello.txt"))
        assert result["content"] == "Hello, World!"
        assert result["size"] == 13
        assert result["encoding"] == "utf-8"

    def test_read_empty_file(self, service: FileService, tmp_workspace: Path):
        result = service.read_file(str(tmp_workspace / "empty.txt"))
        assert result["content"] == ""
        assert result["size"] == 0

    def test_read_nested_file(self, service: FileService, tmp_workspace: Path):
        result = service.read_file(str(tmp_workspace / "subdir" / "nested.txt"))
        assert result["content"] == "nested content"

    def test_read_nonexistent_file(self, service: FileService, tmp_workspace: Path):
        with pytest.raises(FileNotFoundError):
            service.read_file(str(tmp_workspace / "nonexistent.txt"))

    def test_read_directory_raises(self, service: FileService, tmp_workspace: Path):
        with pytest.raises(IsADirectoryError):
            service.read_file(str(tmp_workspace / "subdir"))

    def test_read_disallowed_path(self, service: FileService):
        with pytest.raises(PathNotAllowedError):
            service.read_file("C:/Windows/System32/drivers/etc/hosts")


class TestListDirectory:
    """Tests for directory listing."""

    def test_list_root(self, service: FileService, tmp_workspace: Path):
        result = service.list_directory(str(tmp_workspace))
        names = [e["name"] for e in result["entries"]]
        assert "hello.txt" in names
        assert "subdir" in names
        assert result["count"] > 0

    def test_list_with_pattern(self, service: FileService, tmp_workspace: Path):
        result = service.list_directory(str(tmp_workspace), pattern="*.txt")
        names = [e["name"] for e in result["entries"]]
        assert "hello.txt" in names
        assert "data.json" not in names

    def test_list_recursive(self, service: FileService, tmp_workspace: Path):
        result = service.list_directory(str(tmp_workspace), pattern="*.txt", recursive=True)
        paths = [e["path"] for e in result["entries"]]
        # Should find nested.txt too
        assert any("nested.txt" in p for p in paths)

    def test_list_nonexistent(self, service: FileService, tmp_workspace: Path):
        with pytest.raises(FileNotFoundError):
            service.list_directory(str(tmp_workspace / "no_such_dir"))


class TestExists:
    """Tests for existence checking."""

    def test_file_exists(self, service: FileService, tmp_workspace: Path):
        result = service.exists(str(tmp_workspace / "hello.txt"))
        assert result["exists"] is True
        assert result["is_file"] is True
        assert result["is_dir"] is False

    def test_dir_exists(self, service: FileService, tmp_workspace: Path):
        result = service.exists(str(tmp_workspace / "subdir"))
        assert result["exists"] is True
        assert result["is_file"] is False
        assert result["is_dir"] is True

    def test_not_exists(self, service: FileService, tmp_workspace: Path):
        result = service.exists(str(tmp_workspace / "ghost.txt"))
        assert result["exists"] is False
        assert result["is_file"] is False
        assert result["is_dir"] is False


class TestFileInfo:
    """Tests for file metadata."""

    def test_file_info(self, service: FileService, tmp_workspace: Path):
        result = service.file_info(str(tmp_workspace / "hello.txt"))
        assert result["name"] == "hello.txt"
        assert result["size"] == 13
        assert result["is_file"] is True
        assert result["is_dir"] is False
        assert result["created"] is not None
        assert result["modified"] is not None

    def test_dir_info(self, service: FileService, tmp_workspace: Path):
        result = service.file_info(str(tmp_workspace / "subdir"))
        assert result["name"] == "subdir"
        assert result["is_dir"] is True

    def test_info_nonexistent(self, service: FileService, tmp_workspace: Path):
        with pytest.raises(FileNotFoundError):
            service.file_info(str(tmp_workspace / "missing.txt"))


class TestTree:
    """Tests for directory tree."""

    def test_tree_basic(self, service: FileService, tmp_workspace: Path):
        result = service.tree(str(tmp_workspace))
        tree = result["tree"]
        assert tree["is_dir"] is True
        assert len(tree["children"]) > 0

    def test_tree_max_depth(self, service: FileService, tmp_workspace: Path):
        result = service.tree(str(tmp_workspace), max_depth=1)
        tree = result["tree"]
        # subdir should appear but its children should be empty
        subdirs = [c for c in tree["children"] if c["is_dir"]]
        for sd in subdirs:
            assert sd["children"] == []

    def test_tree_exclude(self, service: FileService, tmp_workspace: Path):
        result = service.tree(str(tmp_workspace), exclude_patterns=["subdir"])
        tree = result["tree"]
        child_names = [c["name"] for c in tree["children"]]
        assert "subdir" not in child_names


class TestSearch:
    """Tests for file search."""

    def test_search_txt(self, service: FileService, tmp_workspace: Path):
        result = service.search(str(tmp_workspace), "*.txt")
        assert result["count"] >= 1
        assert any("hello.txt" in m for m in result["matches"])

    def test_search_recursive(self, service: FileService, tmp_workspace: Path):
        result = service.search(str(tmp_workspace), "**/*.py")
        assert any("code.py" in m for m in result["matches"])

    def test_search_no_results(self, service: FileService, tmp_workspace: Path):
        result = service.search(str(tmp_workspace), "*.xyz")
        assert result["count"] == 0
        assert result["matches"] == []

    def test_search_max_results(self, service: FileService, tmp_workspace: Path):
        result = service.search(str(tmp_workspace), "*", max_results=2)
        assert result["count"] <= 2
        assert result["truncated"] is True
