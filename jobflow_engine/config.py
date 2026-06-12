from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "jobflow_engine"
    environment: str = "local"
    jobs_api_url: str = "http://seek_api:8002"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()