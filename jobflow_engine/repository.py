from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from db_models import (
    DeadLetterJobRecord,
    JobSourceRecord,
    ProcessedJobRecord,
    RawJobRecord,
)
from logger import get_logger
from models import CanonicalJob, FieldMappingRule, JobSource


logger = get_logger(__name__)


class JobSourceRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def seed_default_sources_if_empty(self) -> None:
        existing_sources = await self.get_enabled_sources()

        if existing_sources:
            return

        logger.info("Seeding default job sources")

        seek_source = JobSourceRecord(
            name="seek",
            endpoint_path="/jobs",
            enabled=True,
            timeout_seconds=10,
            field_mapping={
                "external_id": {"path": "id", "required": True, "default": None},
                "title": {"path": "title", "required": True, "default": None},
                "company": {"path": "company", "required": True, "default": None},
                "location": {"path": "location", "required": True, "default": None},
                "description": {"path": "description", "required": False, "default": None},
                "requirements": {"path": "requirements", "required": False, "default": []},
                "responsibilities": {"path": "responsibilities", "required": False, "default": []},
                "employment_type": {"path": "employment_type", "required": False, "default": None},
                "salary_range": {"path": "salary_range", "required": False, "default": None},
                "posted_date": {"path": "posted_date", "required": False, "default": None},
                "apply_url": {"path": "apply_url", "required": False, "default": None},
                "benefits": {"path": "benefits", "required": False, "default": []},
                "experience_years": {"path": "experience_years", "required": False, "default": None},
                "skills": {"path": "skills", "required": True, "default": None},
            },
        )

        self.session.add(seek_source)
        await self.session.commit()

    async def get_enabled_sources(self) -> list[JobSource]:
        result = await self.session.execute(
            select(JobSourceRecord).where(JobSourceRecord.enabled.is_(True))
        )

        records = result.scalars().all()

        return [
            JobSource(
                name=record.name,
                endpoint_path=record.endpoint_path,
                enabled=record.enabled,
                timeout_seconds=record.timeout_seconds,
                field_mapping={
                    canonical_field: FieldMappingRule.model_validate(rule)
                    for canonical_field, rule in record.field_mapping.items()
                },
            )
            for record in records
        ]


class JobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def archive_raw_job(
        self,
        source: str,
        raw_payload: dict[str, Any],
    ) -> None:
        self.session.add(
            RawJobRecord(
                source=source,
                raw_payload=raw_payload,
            )
        )

        await self.session.commit()

    async def processed_job_exists(
        self,
        source: str,
        external_id: str,
    ) -> bool:
        result = await self.session.execute(
            select(ProcessedJobRecord.id).where(
                ProcessedJobRecord.source == source,
                ProcessedJobRecord.external_id == external_id,
            )
        )

        return result.scalar_one_or_none() is not None

    async def save_processed_job(
        self,
        job: CanonicalJob,
        match_score: float | None = None,
    ) -> bool:
        """
        Save a processed job.

        Returns:
            True if inserted.
            False if duplicate.
        """
        canonical_payload = job.model_dump(mode="json")

        record = ProcessedJobRecord(
            source=job.source,
            external_id=job.external_id,
            title=job.title,
            company=job.company,
            location=job.location,
            skills=job.skills,
            canonical_payload=canonical_payload,
            match_score=match_score,
        )

        self.session.add(record)

        try:
            await self.session.commit()
            return True

        except IntegrityError:
            await self.session.rollback()

            logger.info(
                "Duplicate processed job skipped | source=%s | external_id=%s",
                job.source,
                job.external_id,
            )

            return False

    async def save_dead_letter_job(
        self,
        source: str,
        raw_payload: dict[str, Any],
        error_reason: str,
    ) -> None:
        self.session.add(
            DeadLetterJobRecord(
                source=source,
                raw_payload=raw_payload,
                error_reason=error_reason,
            )
        )

        await self.session.commit()

    async def list_processed_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(ProcessedJobRecord)
            .order_by(ProcessedJobRecord.processed_at.desc())
            .limit(limit)
        )

        records = result.scalars().all()

        return [
            {
                "source": record.source,
                "external_id": record.external_id,
                "title": record.title,
                "company": record.company,
                "location": record.location,
                "skills": record.skills,
                "match_score": record.match_score,
                "processed_at": record.processed_at.isoformat(),
            }
            for record in records
        ]

    async def list_dead_letter_jobs(self, limit: int = 50) -> list[dict[str, Any]]:
        result = await self.session.execute(
            select(DeadLetterJobRecord)
            .order_by(DeadLetterJobRecord.failed_at.desc())
            .limit(limit)
        )

        records = result.scalars().all()

        return [
            {
                "source": record.source,
                "raw_payload": record.raw_payload,
                "error_reason": record.error_reason,
                "failed_at": record.failed_at.isoformat(),
            }
            for record in records
        ]