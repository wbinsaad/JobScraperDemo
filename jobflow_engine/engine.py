import asyncio
from typing import Any

from logger import get_logger
from metrics import PipelineMetrics
from queue_manager import JobQueue


logger = get_logger(__name__)


class JobFlowEngine:
    """
    Background processing engine for queued job events.
    """

    def __init__(
        self,
        queue: JobQueue,
        metrics: PipelineMetrics,
        worker_count: int = 1,
    ) -> None:
        self.queue = queue
        self.metrics = metrics
        self.worker_count = worker_count
        self._worker_tasks: set[asyncio.Task[None]] = set()
        self._running = False

    def start(self) -> None:
        """
        Start background worker tasks.

        Keep strong references to created tasks so they are not garbage collected.
        """
        if self._running:
            logger.warning("JobFlowEngine already running")
            return

        self._running = True

        for worker_id in range(1, self.worker_count + 1):
            task = asyncio.create_task(
                self._worker(worker_id),
                name=f"jobflow-worker-{worker_id}",
            )
            self._worker_tasks.add(task)

        logger.info("JobFlowEngine started | worker_count=%s", self.worker_count)

    async def stop(self) -> None:
        """
        Stop background workers gracefully.
        """
        if not self._running:
            return

        self._running = False

        for task in self._worker_tasks:
            task.cancel()

        results = await asyncio.gather(
            *self._worker_tasks,
            return_exceptions=True,
        )

        self._worker_tasks.clear()

        logger.info("JobFlowEngine stopped | task_results=%s", len(results))

    async def enqueue_jobs(self, jobs_by_source: dict[str, list[dict[str, Any]]]) -> int:
        """
        Enqueue fetched jobs for background processing.
        """
        queued_count = 0

        for source_name, jobs in jobs_by_source.items():
            for job in jobs:
                enriched_job = {
                    "source": source_name,
                    "raw_job": job,
                }

                await self.queue.enqueue(enriched_job)
                queued_count += 1

        self.metrics.record_queued(queued_count)

        logger.info(
            "Jobs enqueued | queued_count=%s | queue_depth=%s",
            queued_count,
            self.queue.depth(),
        )

        return queued_count

    async def _worker(self, worker_id: int) -> None:
        """
        Continuously consume jobs from the internal queue.
        """
        logger.info("Worker started | worker_id=%s", worker_id)

        while True:
            try:
                job_event = await self.queue.dequeue()
                await self._process_job(job_event, worker_id)

            except asyncio.CancelledError:
                logger.info("Worker cancelled | worker_id=%s", worker_id)
                raise

            except Exception:
                self.metrics.record_failed()
                logger.exception("Unexpected worker error | worker_id=%s", worker_id)

            finally:
                try:
                    self.queue.mark_done()
                except ValueError:
                    logger.exception("Queue task_done called incorrectly")

    async def _process_job(
        self,
        job_event: dict[str, Any],
        worker_id: int,
    ) -> None:
        """
        Temporary processing logic.
        """
        source = job_event.get("source", "unknown")
        raw_job = job_event.get("raw_job", {})

        job_id = raw_job.get("job_id") or raw_job.get("id") or "unknown"

        logger.info(
            "Processing job | worker_id=%s | source=%s | job_id=%s",
            worker_id,
            source,
            job_id,
        )

        # Simulate async processing point.
        await asyncio.sleep(5)

        self.metrics.record_processed()

        logger.info(
            "Processed job | worker_id=%s | source=%s | job_id=%s",
            worker_id,
            source,
            job_id,
        )