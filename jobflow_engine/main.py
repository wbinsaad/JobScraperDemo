from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from jobs_client import JobsClient
from repository import JobSourceRepository
from logger import setup_logging, get_logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()

    logger = get_logger(__name__)
    logger.info("Starting %s", settings.app_name)

    yield

    logger.info("Shutting down %s", settings.app_name)

setup_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="jobflow_engine",
    lifespan=lifespan,
)

@app.get("/health")
def health_check():
    logger = get_logger(__name__)
    logger.debug("Health check requested")
    return {"status": "healthy"}

@app.post("/fetch-jobs")
async def fetch_jobs():
    repository = JobSourceRepository()
    sources = await repository.get_enabled_sources()

    client = JobsClient()
    jobs_by_source = await client.fetch_all_sources(sources)

    counts_by_source = {
        source_name: len(jobs)
        for source_name, jobs in jobs_by_source.items()
    }

    total_fetched = sum(counts_by_source.values())

    logger.info(
        "Fetch jobs completed | sources=%s | total_fetched=%s",
        counts_by_source,
        total_fetched,
    )

    return {
        "status": "success",
        "sources": counts_by_source,
        "total_fetched": total_fetched,
    }