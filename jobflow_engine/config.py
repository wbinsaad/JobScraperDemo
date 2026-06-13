from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "jobflow_engine"
    environment: str = "local"
    jobs_api_url: str = "http://seek_api:8002"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/jobflow"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()