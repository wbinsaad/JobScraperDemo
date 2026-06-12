from models import JobSource


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
            ),
            JobSource(
                name="seek",
                endpoint_path="/jobs",
                enabled=True,
                timeout_seconds=10,
            ),
        ]