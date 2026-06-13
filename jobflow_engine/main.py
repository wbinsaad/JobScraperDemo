from contextlib import asynccontextmanager
from typing import Any

import httpx
from fastapi import FastAPI, Request

from config import settings
from engine import JobFlowEngine
from jobs_client import JobsClient
from logger import get_logger, setup_logging
from metrics import PipelineMetrics
from queue_manager import JobQueue
from repository import JobSourceRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    logger = get_logger(__name__)
    logger.info("Starting %s", settings.app_name)

    http_client = httpx.AsyncClient()
    queue = JobQueue(maxsize=1_000)
    metrics = PipelineMetrics()
    engine = JobFlowEngine(
        queue=queue,
        metrics=metrics,
        worker_count=1,
    )

    engine.start()

    app.state.http_client = http_client
    app.state.queue = queue
    app.state.metrics = metrics
    app.state.engine = engine
    app.state.source_repository = JobSourceRepository()
    app.state.jobs_client = JobsClient(http_client=http_client)

    try:
        yield

    finally:
        logger.info("Shutting down %s", settings.app_name)

        await engine.stop()
        await http_client.aclose()

        logger.info("Shutdown complete | service=%s", settings.app_name)


app = FastAPI(
    title="jobflow_engine",
    lifespan=lifespan,
)

@app.get("/health")
def health_check() -> dict[str, str]:
    logger = get_logger(__name__)
    logger.debug("Health check requested")
    return {"status": "healthy"}

@app.post("/fetch-jobs")
async def fetch_jobs(request: Request) -> dict[str, Any]:
    logger = get_logger(__name__)

    repository: JobSourceRepository = request.app.state.source_repository
    jobs_client: JobsClient = request.app.state.jobs_client
    engine: JobFlowEngine = request.app.state.engine
    metrics: PipelineMetrics = request.app.state.metrics
    queue: JobQueue = request.app.state.queue

    sources = await repository.get_enabled_sources()
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