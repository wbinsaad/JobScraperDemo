from models import FieldMappingRule
from transformer import JobTransformer


def test_seek_job_transforms_to_canonical_payload() -> None:
    raw_seek_job = {
        "id": "8a9e687f-5ac7-439e-bc33-faaa06f3c21f",
        "title": "Developer",
        "company": "Data Processors Pty Ltd",
        "location": "Melbourne, VIC, Australia",
        "description": "Build and maintain pipelines.",
        "requirements": ["Python", "SQL", "Docker"],
        "responsibilities": ["Validate and transform data", "Deploy pipelines"],
        "employment_type": "Full-time",
        "salary_range": "Negotiable",
        "posted_date": "2026-06-01",
        "apply_url": None,
        "benefits": None,
        "experience_years": None,
        "skills": ["Python", "SQL", "Docker"],
    }

    field_mapping = {
        "external_id": FieldMappingRule(path="id", required=True),
        "title": FieldMappingRule(path="title", required=True),
        "company": FieldMappingRule(path="company", required=True),
        "location": FieldMappingRule(path="location", required=True),
        "description": FieldMappingRule(path="description", required=False),
        "requirements": FieldMappingRule(path="requirements", required=False, default=[]),
        "responsibilities": FieldMappingRule(path="responsibilities", required=False, default=[]),
        "employment_type": FieldMappingRule(path="employment_type", required=False),
        "salary_range": FieldMappingRule(path="salary_range", required=False),
        "posted_date": FieldMappingRule(path="posted_date", required=False),
        "apply_url": FieldMappingRule(path="apply_url", required=False),
        "benefits": FieldMappingRule(path="benefits", required=False, default=[]),
        "experience_years": FieldMappingRule(path="experience_years", required=False),
        "skills": FieldMappingRule(path="skills", required=True),
    }

    transformer = JobTransformer()

    result = transformer.transform(
        source="seek",
        raw_job=raw_seek_job,
        field_mapping=field_mapping,
    )

    assert result["source"] == "seek"
    assert result["external_id"] == "8a9e687f-5ac7-439e-bc33-faaa06f3c21f"
    assert result["title"] == "Developer"
    assert result["company"] == "Data Processors Pty Ltd"
    assert result["location"] == "Melbourne, VIC, Australia"
    assert result["requirements"] == ["Python", "SQL", "Docker"]
    assert result["skills"] == ["Python", "SQL", "Docker"]