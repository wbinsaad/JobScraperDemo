from models import FieldMappingRule, JobSource


class JobSourceRepository:
    """
    Temporary source repository.

    Later this should read from the job_sources table.
    """

    async def get_enabled_sources(self) -> list[JobSource]:
        return [
            JobSource(
                name="linkedin",
                endpoint_path="/jobs",
                enabled=True,
                timeout_seconds=10,
                field_mapping={
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
                },
            ),
            JobSource(
                name="seek",
                endpoint_path="/jobs",
                enabled=True,
                timeout_seconds=10,
                field_mapping={
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
                },
            ),
        ]