from pydantic import BaseModel, Field


class JobSource(BaseModel):
    name: str = Field(min_length=1)
    endpoint_path: str = Field(min_length=1)
    enabled: bool = True
    timeout_seconds: int = Field(default=10, ge=1, le=60)