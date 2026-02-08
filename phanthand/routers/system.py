"""System endpoints (health check, etc.)."""

import socket
import time

from fastapi import APIRouter

from .. import __version__
from ..models import ApiResponse, HealthData

router = APIRouter(tags=["system"])

_start_time = time.time()


@router.get("/health", response_model=ApiResponse[HealthData])
async def health():
    """Health check endpoint (no authentication required)."""
    return ApiResponse(
        success=True,
        data=HealthData(
            status="ok",
            version=__version__,
            hostname=socket.gethostname(),
            uptime_seconds=round(time.time() - _start_time, 2),
        ),
    )
