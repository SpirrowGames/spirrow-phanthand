"""Phanthand - Lightweight file access API server."""

import uvicorn
from fastapi import FastAPI

from . import __version__
from .config import get_config
from .routers import files, system

app = FastAPI(
    title="Phanthand",
    description="Lightweight file access API for development PCs",
    version=__version__,
)

# Routers
app.include_router(system.router)
app.include_router(files.router)


def main():
    """Entry point for running the server."""
    config = get_config()
    print(f"Phanthand v{__version__} starting...")
    print(f"  Host: {config.server.host}")
    print(f"  Port: {config.server.port}")
    print(f"  Allowed paths: {config.security.allowed_paths}")
    uvicorn.run(
        "phanthand.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=False,
    )


if __name__ == "__main__":
    main()
