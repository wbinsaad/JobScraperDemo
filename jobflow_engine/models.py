# jobflow_engine/models.py

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class FieldMappingRule(BaseModel):
    """
    Defines how one canonical field maps to one raw source field.
    """

    model_config = ConfigDict(extra="forbid")

    path: str = Field(min_length=1)
    required: bool = True
    default: Any = None


class JobSource(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    endpoint_path: str = Field(min_length=1)
    enabled: bool = True
    timeout_seconds: int = Field(default=10, ge=1, le=60)
    field_mapping: dict[str, FieldMappingRule]


class SourceJobBatch(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: JobSource
    jobs: list[dict[str, Any]]


class QueuedJobEvent(BaseModel):
    """
    Internal queue envelope.
    """

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    raw_job: dict[str, Any]
    field_mapping: dict[str, FieldMappingRule]


class CanonicalJob(BaseModel):
    """
    Normalised internal job model used by jobflow_engine.

    This is the clean schema after source-specific transformation.
    """

    model_config = ConfigDict(extra="forbid")

    source: str = Field(min_length=1)
    external_id: str = Field(min_length=1)

    title: str = Field(min_length=1)
    company: str = Field(min_length=1)
    location: str = Field(min_length=1)

    description: str | None = None
    requirements: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)

    employment_type: str | None = None
    salary_range: str | None = None
    posted_date: str | None = None
    apply_url: HttpUrl | None = None
    benefits: list[str] = Field(default_factory=list)
    experience_years: int | None = None

    skills: list[str] = Field(min_length=1)

    @field_validator("requirements", "responsibilities", "benefits", mode="before")
    @classmethod
    def none_to_empty_list(cls, value: Any) -> list[str]:
        if value is None:
            return []

        if isinstance(value, list):
            return [
                str(item).strip()
                for item in value
                if str(item).strip()
            ]

        return [str(value).strip()] if str(value).strip() else []

    @field_validator("skills", mode="before")
    @classmethod
    def validate_skills(cls, value: Any) -> list[str]:
        if not isinstance(value, list):
            raise ValueError("skills must be a list")

        cleaned_skills = [
            str(skill).strip().lower()
            for skill in value
            if str(skill).strip()
        ]

        if not cleaned_skills:
            raise ValueError("skills must contain at least one non-empty skill")

        return cleaned_skills