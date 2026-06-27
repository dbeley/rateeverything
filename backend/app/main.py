"""Main FastAPI application"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import get_settings
from app.database import init_db, close_db

# Routes
from app.routes_types import router as types_router
from app.routes_entities import router as entities_router
from app.routes_ratings import router as ratings_router
from app.routes_relations import router as relations_router
from app.routes_llm import router as llm_router
from app.routes_charts import router as charts_router
from app.routes_auth import router as auth_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown"""
    settings = get_settings()
    logger.info(f"Starting {settings.app_name}")
    try:
        await init_db()
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.warning(f"Database init (may not be available yet): {e}")
    yield
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="RateEverything API",
    description="Universal rating platform — rate everything that exists",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(types_router)
app.include_router(entities_router)
app.include_router(ratings_router)
app.include_router(relations_router)
app.include_router(llm_router)
app.include_router(charts_router)
app.include_router(auth_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "app": "RateEverything API", "version": "0.1.0"}
