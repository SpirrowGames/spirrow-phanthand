"""File operations service for Phanthand."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from ..config import get_config


class PathNotAllowedError(Exception):
    """Raised when a path is outside allowed directories."""

    def __init__(self, path: str):
        self.path = path
        super().__init__(f"Path not allowed: {path}")


class FileService:
    """Provides safe file read operations within allowed paths."""

    def validate_path(self, path: str) -> Path:
        """Resolve and validate that path is within allowed directories.

        Args:
            path: Absolute path string to validate.

        Returns:
            Resolved Path object.

        Raises:
            PathNotAllowedError: If the path is outside all allowed directories.
        """
        config = get_config()
        resolved = Path(path).resolve()

        for allowed in config.security.allowed_paths:
            allowed_resolved = Path(allowed).resolve()
            try:
                resolved.relative_to(allowed_resolved)
                return resolved
            except ValueError:
                continue

        raise PathNotAllowedError(str(resolved))

    def read_file(self, path: str, encoding: str = "utf-8") -> dict:
        """Read a text file and return its content.

        Args:
            path: Absolute file path.
            encoding: Text encoding (default utf-8).

        Returns:
            Dict with path, content, size, encoding.

        Raises:
            PathNotAllowedError: If path is outside allowed directories.
            FileNotFoundError: If the file does not exist.
            IsADirectoryError: If the path points to a directory.
            ValueError: If the file exceeds max size.
        """
        resolved = self.validate_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"File not found: {resolved}")

        if resolved.is_dir():
            raise IsADirectoryError(f"Path is a directory: {resolved}")

        config = get_config()
        size = resolved.stat().st_size
        if size > config.security.max_file_size_bytes:
            raise ValueError(
                f"File size {size} bytes exceeds limit of "
                f"{config.security.max_file_size_mb} MB"
            )

        content = resolved.read_text(encoding=encoding)
        return {
            "path": str(resolved),
            "content": content,
            "size": size,
            "encoding": encoding,
        }

    def list_directory(
        self,
        path: str,
        pattern: str = "*",
        recursive: bool = False,
    ) -> dict:
        """List files and directories matching a pattern.

        Args:
            path: Absolute directory path.
            pattern: Glob pattern (default "*").
            recursive: Whether to search subdirectories.

        Returns:
            Dict with path, entries list, count.
        """
        resolved = self.validate_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"Directory not found: {resolved}")

        if not resolved.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {resolved}")

        entries = []
        if recursive:
            matches = sorted(resolved.rglob(pattern))
        else:
            matches = sorted(resolved.glob(pattern))

        for item in matches:
            entry = {
                "name": item.name,
                "path": str(item),
                "is_dir": item.is_dir(),
            }
            if item.is_file():
                try:
                    entry["size"] = item.stat().st_size
                except OSError:
                    entry["size"] = None
            entries.append(entry)

        return {
            "path": str(resolved),
            "entries": entries,
            "count": len(entries),
        }

    def exists(self, path: str) -> dict:
        """Check if a file or directory exists.

        Args:
            path: Absolute path to check.

        Returns:
            Dict with path, exists, is_file, is_dir.
        """
        resolved = self.validate_path(path)
        exists = resolved.exists()
        return {
            "path": str(resolved),
            "exists": exists,
            "is_file": resolved.is_file() if exists else False,
            "is_dir": resolved.is_dir() if exists else False,
        }

    def file_info(self, path: str) -> dict:
        """Get metadata about a file or directory.

        Args:
            path: Absolute path.

        Returns:
            Dict with path, name, size, timestamps, type, readonly.
        """
        resolved = self.validate_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"Path not found: {resolved}")

        stat = resolved.stat()

        created = datetime.fromtimestamp(stat.st_ctime, tz=timezone.utc)
        modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)

        # On Windows, check if the file is read-only
        readonly = not os.access(resolved, os.W_OK)

        return {
            "path": str(resolved),
            "name": resolved.name,
            "size": stat.st_size,
            "created": created,
            "modified": modified,
            "is_file": resolved.is_file(),
            "is_dir": resolved.is_dir(),
            "readonly": readonly,
        }

    def tree(
        self,
        path: str,
        max_depth: int = 3,
        exclude_patterns: Optional[List[str]] = None,
    ) -> dict:
        """Build a recursive directory tree.

        Args:
            path: Absolute directory path.
            max_depth: Maximum depth to traverse.
            exclude_patterns: Directory names to skip.

        Returns:
            Dict with path and tree structure.
        """
        if exclude_patterns is None:
            exclude_patterns = [
                ".git", "__pycache__", "node_modules",
                ".vs", "Binaries", "Intermediate",
            ]

        resolved = self.validate_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"Directory not found: {resolved}")

        if not resolved.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {resolved}")

        def _build_tree(dir_path: Path, depth: int) -> dict:
            node = {
                "name": dir_path.name,
                "path": str(dir_path),
                "is_dir": True,
                "children": [],
            }

            if depth >= max_depth:
                return node

            try:
                items = sorted(dir_path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
            except PermissionError:
                return node

            for item in items:
                if item.name in exclude_patterns:
                    continue

                if item.is_dir():
                    child = _build_tree(item, depth + 1)
                    node["children"].append(child)
                else:
                    node["children"].append({
                        "name": item.name,
                        "path": str(item),
                        "is_dir": False,
                        "children": None,
                    })

            return node

        tree = _build_tree(resolved, 0)
        return {
            "path": str(resolved),
            "tree": tree,
        }

    def search(
        self,
        path: str,
        pattern: str,
        max_results: int = 100,
    ) -> dict:
        """Search for files matching a glob pattern.

        Args:
            path: Root directory to search from.
            pattern: Glob pattern (e.g. '*.cpp', '**/*.h').
            max_results: Maximum number of results.

        Returns:
            Dict with path, pattern, matches, count, truncated.
        """
        resolved = self.validate_path(path)

        if not resolved.exists():
            raise FileNotFoundError(f"Directory not found: {resolved}")

        if not resolved.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {resolved}")

        matches = []
        truncated = False

        for item in resolved.rglob(pattern):
            matches.append(str(item))
            if len(matches) >= max_results:
                truncated = True
                break

        return {
            "path": str(resolved),
            "pattern": pattern,
            "matches": matches,
            "count": len(matches),
            "truncated": truncated,
        }
