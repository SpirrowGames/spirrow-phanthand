"""File operation endpoints."""

from fastapi import APIRouter, Depends

from ..auth import verify_api_key
from ..models import (
    ApiResponse,
    FileExistsData,
    FileExistsRequest,
    FileInfoData,
    FileInfoRequest,
    FileListData,
    FileListRequest,
    FileReadData,
    FileReadRequest,
    FileSearchData,
    FileSearchRequest,
    FileTreeData,
    FileTreeRequest,
)
from ..services.file_service import FileService, PathNotAllowedError

router = APIRouter(prefix="/files", tags=["files"])

_service = FileService()


def _error_response(e: Exception) -> ApiResponse:
    """Build a standard error response from an exception."""
    if isinstance(e, PathNotAllowedError):
        return ApiResponse(success=False, error=f"Path not allowed: {e.path}")
    if isinstance(e, FileNotFoundError):
        return ApiResponse(success=False, error=str(e))
    if isinstance(e, (IsADirectoryError, NotADirectoryError)):
        return ApiResponse(success=False, error=str(e))
    if isinstance(e, ValueError):
        return ApiResponse(success=False, error=str(e))
    if isinstance(e, PermissionError):
        return ApiResponse(success=False, error=f"Permission denied: {e}")
    if isinstance(e, UnicodeDecodeError):
        return ApiResponse(success=False, error=f"Encoding error: {e}")
    return ApiResponse(success=False, error=f"Unexpected error: {type(e).__name__}: {e}")


@router.post("/read", response_model=ApiResponse[FileReadData])
async def read_file(req: FileReadRequest, _: str = Depends(verify_api_key)):
    """Read a text file."""
    try:
        result = _service.read_file(req.path, req.encoding)
        return ApiResponse(success=True, data=FileReadData(**result))
    except Exception as e:
        return _error_response(e)


@router.post("/list", response_model=ApiResponse[FileListData])
async def list_directory(req: FileListRequest, _: str = Depends(verify_api_key)):
    """List files and directories."""
    try:
        result = _service.list_directory(req.path, req.pattern, req.recursive)
        return ApiResponse(success=True, data=FileListData(**result))
    except Exception as e:
        return _error_response(e)


@router.post("/exists", response_model=ApiResponse[FileExistsData])
async def file_exists(req: FileExistsRequest, _: str = Depends(verify_api_key)):
    """Check if a file or directory exists."""
    try:
        result = _service.exists(req.path)
        return ApiResponse(success=True, data=FileExistsData(**result))
    except Exception as e:
        return _error_response(e)


@router.post("/info", response_model=ApiResponse[FileInfoData])
async def file_info(req: FileInfoRequest, _: str = Depends(verify_api_key)):
    """Get file metadata."""
    try:
        result = _service.file_info(req.path)
        return ApiResponse(success=True, data=FileInfoData(**result))
    except Exception as e:
        return _error_response(e)


@router.post("/tree", response_model=ApiResponse[FileTreeData])
async def file_tree(req: FileTreeRequest, _: str = Depends(verify_api_key)):
    """Get a recursive directory tree."""
    try:
        result = _service.tree(req.path, req.max_depth, req.exclude_patterns)
        return ApiResponse(success=True, data=FileTreeData(**result))
    except Exception as e:
        return _error_response(e)


@router.post("/search", response_model=ApiResponse[FileSearchData])
async def file_search(req: FileSearchRequest, _: str = Depends(verify_api_key)):
    """Search for files matching a glob pattern."""
    try:
        result = _service.search(req.path, req.pattern, req.max_results)
        return ApiResponse(success=True, data=FileSearchData(**result))
    except Exception as e:
        return _error_response(e)
