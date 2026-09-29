from fastapi import FastAPI
from .features.temporal_complexity.router import router as temporal_router
from app.features.auth.router import router as user_router
from .features.spatial_complexity.router import router as spatial_router
from .core import setup_middlewares
from contextlib import asynccontextmanager
from .core import Database
from typing import AsyncGenerator

db = Database()

API_PREFIX = "/api"
ANALYZE_PREFIX = "/analyze"


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    print("Application starting...")
    await db.init_db()

    yield

    print("Application shutting down...")
    await db.shutdown_db()


app = FastAPI(title="BigDSA", version="1.0.0", lifespan=lifespan)

setup_middlewares(app)

app.include_router(temporal_router, prefix=f"{API_PREFIX}{ANALYZE_PREFIX}")
app.include_router(spatial_router, prefix=f"{API_PREFIX}{ANALYZE_PREFIX}")
app.include_router(user_router, prefix=API_PREFIX)


@app.get("/api/health")
async def health():
    db_ok = await db.ping()
    return {"status": "ok", "database": {"status": db_ok}}
