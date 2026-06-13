from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class JobSourceRecord(Base):
    __tablename__ = "job_sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    endpoint_path: Mapped[str] = mapped_column(String(255), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    timeout_seconds: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    field_mapping: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class RawJobRecord(Base):
    __tablename__ = "raw_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    source: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class ProcessedJobRecord(Base):
    __tablename__ = "processed_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    source: Mapped[str] = mapped_column(String(100), nullable=False)
    external_id: Mapped[str] = mapped_column(String(255), nullable=False)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    company: Mapped[str] = mapped_column(String(255), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)

    skills: Mapped[list[str]] = mapped_column(JSONB, nullable=False)
    canonical_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)

    match_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "source",
            "external_id",
            name="uq_processed_jobs_source_external_id",
        ),
    )


class DeadLetterJobRecord(Base):
    __tablename__ = "dead_letter_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    source: Mapped[str] = mapped_column(String(100), nullable=False)
    raw_payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    error_reason: Mapped[str] = mapped_column(Text, nullable=False)

    failed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )