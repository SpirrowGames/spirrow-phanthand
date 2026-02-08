"""Pydantic request/response models for Phanthand API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


# ── Generic API Response ──────────────────────────────────────────


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response wrapper."""

    success: bool = True
    data: Optional[T] = None
    error: Optional[str] = None


# ── Health ────────────────────────────────────────────────────────


class HealthData(BaseModel):
    status: str = "ok"
    version: str
    hostname: str
    uptime_seconds: float


# ── File Read ─────────────────────────────────────────────────────


class FileReadRequest(BaseModel):
    path: str = Field(..., description="Absolute file path to read")
    encoding: str = Field("utf-8", description="Text encoding")


class FileReadData(BaseModel):
    path: str
    content: str
    size: int
    encoding: str


# ── File List ─────────────────────────────────────────────────────


class FileListRequest(BaseModel):
    path: str = Field(..., description="Absolute directory path")
    pattern: str = Field("*", description="Glob pattern")
    recursive: bool = Field(False, description="Search subdirectories")


class FileListEntry(BaseModel):
    name: str
    path: str
    is_dir: bool
    size: Optional[int] = None


class FileListData(BaseModel):
    path: str
    entries: List[FileListEntry]
    count: int


# ── File Exists ───────────────────────────────────────────────────


class FileExistsRequest(BaseModel):
    path: str = Field(..., description="Absolute path to check")


class FileExistsData(BaseModel):
    path: str
    exists: bool
    is_file: bool
    is_dir: bool


# ── File Info ─────────────────────────────────────────────────────


class FileInfoRequest(BaseModel):
    path: str = Field(..., description="Absolute file path")


class FileInfoData(BaseModel):
    path: str
    name: str
    size: int
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    is_file: bool
    is_dir: bool
    readonly: bool


# ── File Tree ─────────────────────────────────────────────────────


class FileTreeRequest(BaseModel):
    path: str = Field(..., description="Absolute directory path")
    max_depth: int = Field(3, description="Maximum depth to traverse")
    exclude_patterns: List[str] = Field(
        default_factory=lambda: [".git", "__pycache__", "node_modules", ".vs", "Binaries", "Intermediate"],
        description="Directory names to exclude",
    )


class TreeNode(BaseModel):
    name: str
    path: str
    is_dir: bool
    children: Optional[List[TreeNode]] = None


class FileTreeData(BaseModel):
    path: str
    tree: TreeNode


# ── File Search ───────────────────────────────────────────────────


class FileSearchRequest(BaseModel):
    path: str = Field(..., description="Root directory to search from")
    pattern: str = Field(..., description="Glob pattern (e.g. '*.cpp', '**/*.h')")
    max_results: int = Field(100, description="Max number of results")


class FileSearchData(BaseModel):
    path: str
    pattern: str
    matches: List[str]
    count: int
    truncated: bool
