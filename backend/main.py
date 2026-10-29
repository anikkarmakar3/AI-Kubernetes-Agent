from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from api.health import router as health_router
from api.investigation import router as investigation_router
from core.config import settings
from core.logging import configure_logging


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    logger.info("AI Kubernetes Agent backend started")
    yield


app = FastAPI(
    title="AI Kubernetes Agent",
    description="On-demand Kubernetes troubleshooting orchestrator",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(investigation_router)
