import pytest

from validation import JobValidationError, JobValidator


def test_invalid_canonical_job_fails_validation_when_title_is_missing() -> None:
    invalid_job = {
        "source": "seek",
        "external_id": "job-001",
        "title": "",
        "company": "Data Processors Pty Ltd",
        "location": "Melbourne, VIC, Australia",
        "skills": ["Python", "SQL"],
    }

    validator = JobValidator()

    with pytest.raises(JobValidationError):
        validator.validate_canonical_job(invalid_job)