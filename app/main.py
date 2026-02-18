import logging
import os
from pathlib import Path

from contextlib import asynccontextmanager

from fastapi import FastAPI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.storage.db import init_db


def _get_static_path() -> Path:
    """Return path to built frontend. Overridable for tests."""
    return Path(__file__).resolve().parent.parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    token = os.environ.get("HF_TOKEN", "").strip()
    if not token:
        raise RuntimeError(
            "HF_TOKEN environment variable is required. "
            "Set it in .env or pass -e HF_TOKEN=... when running."
        )
    await init_db()
    yield


def create_app(static_dir: Path | None = None) -> FastAPI:
    """Create FastAPI app. static_dir overrides static path (for tests)."""
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    # Mount static last so API routes take precedence
    static_path = static_dir if static_dir is not None else _get_static_path()
    if static_path.exists():
        app.mount("/", StaticFiles(directory=str(static_path), html=True), name="static")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return app


app = create_app()
