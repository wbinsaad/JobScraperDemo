# jobflow_engine/engine.py

import asyncio
from typing import Any

from logger import get_logger
from metrics import PipelineMetrics
from queue_manager import JobQueue
from transformer import JobTransformationError, JobTransformer
from validation import JobValidationError, JobValidator
from models import SourceJobBatch

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
        self.validator = JobValidator()
        self.transformer = JobTransformer()
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

        await asyncio.gather(
            *self._worker_tasks,
            return_exceptions=True,
        )

        self._worker_tasks.clear()

        logger.info("JobFlowEngine stopped")

    async def enqueue_jobs(self, source_batches: list[SourceJobBatch]) -> int:
        queued_count = 0

        for batch in source_batches:
            for job in batch.jobs:
                await self.queue.enqueue(
                    {
                        "source": batch.source.name,
                        "raw_job": job,
                        "field_mapping": batch.source.field_mapping,
                    }
                )
                queued_count += 1

        self.metrics.record_queued(queued_count)
        
        """
        queued_count = total number of jobs you added to the queue
        queue_depth  = number of jobs still waiting in the queue right now
        """

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
        try:
            queue_event = self.validator.validate_queue_event(job_event)

            transformed_job = self.transformer.transform(
                source=queue_event.source,
                raw_job=queue_event.raw_job,
                field_mapping=queue_event.field_mapping,
            )

            canonical_job = self.validator.validate_canonical_job(transformed_job)

        except (JobValidationError, JobTransformationError) as exc:
            self.metrics.record_failed()

            logger.warning(
                "Job rejected | worker_id=%s | reason=%s | raw_event=%s",
                worker_id,
                str(exc),
                job_event,
            )
            return

        logger.info(
            "validating and Processing job | worker_id=%s | source=%s | external_id=%s | title=%s",
            worker_id,
            canonical_job.source,
            canonical_job.external_id,
            canonical_job.title,
        )

        # Simulate async processing point.
        await asyncio.sleep(5)

        self.metrics.record_processed()

        logger.info(
            "Processed job | worker_id=%s | source=%s | job_id=%s",
            worker_id,
            canonical_job.source,
            canonical_job.external_id,
        )