from typing import Any

from pydantic import ValidationError

from logger import get_logger
from models import CanonicalJob, QueuedJobEvent


logger = get_logger(__name__)


class JobValidationError(Exception):
    """Raised when a job fails validation."""


class JobValidator:
    """
    Validates queue events and canonical jobs.
    """

    def validate_queue_event(self, job_event: dict[str, Any]) -> QueuedJobEvent:
        try:
            return QueuedJobEvent.model_validate(job_event)

        except ValidationError as exc:
            logger.warning(
                "Invalid queue event | errors=%s",
                exc.errors(),
            )
            raise JobValidationError("Invalid queue event") from exc

    def validate_canonical_job(self, job: dict[str, Any]) -> CanonicalJob:
        try:
            return CanonicalJob.model_validate(job)

        except ValidationError as exc:
            logger.warning(
                "Invalid canonical job | errors=%s",
                exc.errors(),
            )
            raise JobValidationError("Invalid canonical job") from exc