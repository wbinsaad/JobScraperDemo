from models import CanonicalJob
from repository import JobRepository


def build_canonical_job(
    external_id: str = "8a9e687f-5ac7-439e-bc33-faaa06f3c21f",
) -> CanonicalJob:
    return CanonicalJob(
        source="seek",
        external_id=external_id,
        title="Developer",
        company="Data Processors Pty Ltd",
        location="Melbourne, VIC, Australia",
        description="Build and maintain pipelines.",
        requirements=["Python", "SQL", "Docker"],
        responsibilities=["Validate and transform data", "Deploy pipelines"],
        employment_type="Full-time",
        salary_range="Negotiable",
        posted_date="2026-06-01",
        apply_url=None,
        benefits=[],
        experience_years=None,
        skills=["Python", "SQL", "Docker"],
    )


async def test_repository_saves_processed_job(db_session) -> None:
    repository = JobRepository(db_session)
    job = build_canonical_job()

    inserted = await repository.save_processed_job(
        job=job,
        match_score=85.0,
    )

    jobs = await repository.list_processed_jobs()

    assert inserted is True
    assert len(jobs) == 1
    assert jobs[0]["source"] == "seek"
    assert jobs[0]["external_id"] == job.external_id
    assert jobs[0]["title"] == "Developer"
    assert jobs[0]["match_score"] == 85.0


async def test_repository_skips_duplicate_processed_job(db_session) -> None:
    repository = JobRepository(db_session)
    job = build_canonical_job()

    first_insert = await repository.save_processed_job(job=job, match_score=85.0)
    second_insert = await repository.save_processed_job(job=job, match_score=85.0)

    jobs = await repository.list_processed_jobs()

    assert first_insert is True
    assert second_insert is False
    assert len(jobs) == 1


async def test_repository_saves_dead_letter_job(db_session) -> None:
    repository = JobRepository(db_session)

    raw_payload = {
        "id": "",
        "title": "",
        "company": "Data Processors Pty Ltd",
        "location": "Melbourne, VIC, Australia",
        "skills": [],
    }

    await repository.save_dead_letter_job(
        source="seek",
        raw_payload=raw_payload,
        error_reason="Invalid canonical job",
    )

    dead_letters = await repository.list_dead_letter_jobs()

    assert len(dead_letters) == 1
    assert dead_letters[0]["source"] == "seek"
    assert dead_letters[0]["raw_payload"] == raw_payload
    assert dead_letters[0]["error_reason"] == "Invalid canonical job"