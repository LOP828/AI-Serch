from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Critical Search Layer"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CSL_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
