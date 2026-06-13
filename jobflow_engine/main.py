from database import AsyncSessionLocal
from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import Depends, FastAPI, Request
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database import close_database, get_session, init_database
from engine import JobFlowEngine
from jobs_client import JobsClient
from logger import get_logger, setup_logging
from metrics import PipelineMetrics
from queue_manager import JobQueue
from repository import JobRepository, JobSourceRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    logger = get_logger(__name__)
    logger.info("Starting %s", settings.app_name)
    await init_database()

    http_client = httpx.AsyncClient()
    queue = JobQueue(maxsize=1_000)
    metrics = PipelineMetrics()
    engine = JobFlowEngine(
        queue=queue,
        metrics=metrics,
        session_factory=AsyncSessionLocal,
        worker_count=1,
    )

    engine.start()

    app.state.http_client = http_client
    app.state.queue = queue
    app.state.metrics = metrics
    app.state.engine = engine
    app.state.jobs_client = JobsClient(http_client=http_client)

    try:
        yield

    finally:
        logger.info("Shutting down %s", settings.app_name)

        await engine.stop()
        await http_client.aclose()
        await close_database()

        logger.info("Shutdown complete | service=%s", settings.app_name)


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

@app.get("/health")
def health_check() -> dict[str, str]:
    return {
        "service": settings.app_name,
        "status": "healthy",
        "environment": settings.environment,
    }


@app.post("/seed-sources")
async def seed_sources(
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    repository = JobSourceRepository(session)
    await repository.seed_default_sources_if_empty()

    return {
        "status": "success",
        "message": "Default sources seeded if empty",
    }


@app.post("/fetch-jobs")
async def fetch_jobs(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    logger = get_logger(__name__)

    source_repository = JobSourceRepository(session)

    sources = await source_repository.get_enabled_sources()

    if not sources:
        logger.warning("No enabled job sources found")
        return {
            "status": "no_sources",
            "sources": {},
            "fetched_count": 0,
            "queued_count": 0,
            "queue_depth": request.app.state.queue.depth(),
        }

    jobs_client: JobsClient = request.app.state.jobs_client
    engine: JobFlowEngine = request.app.state.engine
    metrics: PipelineMetrics = request.app.state.metrics
    queue: JobQueue = request.app.state.queue

    source_batches = await jobs_client.fetch_all_sources(sources)

    fetched_count = sum(len(batch.jobs) for batch in source_batches)
    metrics.record_fetched(fetched_count)

    queued_count = await engine.enqueue_jobs(source_batches)

    logger.info(
        "Fetch jobs completed | fetched_count=%s | queued_count=%s | queue_depth=%s",
        fetched_count,
        queued_count,
        queue.depth(),
    )

    return {
        "status": "success",
        "sources": {
            batch.source.name: len(batch.jobs)
            for batch in source_batches
        },
        "fetched_count": fetched_count,
        "queued_count": queued_count,
        "queue_depth": queue.depth(),
    }


@app.get("/metrics")
def get_metrics(request: Request) -> dict[str, int]:
    metrics: PipelineMetrics = request.app.state.metrics
    queue: JobQueue = request.app.state.queue

    return metrics.snapshot(queue_depth=queue.depth())


@app.get("/jobs")
async def get_jobs(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    repository = JobRepository(session)
    return await repository.list_processed_jobs()


@app.get("/dead-letter")
async def get_dead_letter_jobs(
    session: AsyncSession = Depends(get_session),
) -> list[dict[str, Any]]:
    repository = JobRepository(session)
    return await repository.list_dead_letter_jobs()