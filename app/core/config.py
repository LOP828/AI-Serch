from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Critical Search Layer"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    search_provider: str = "static"
    search_api_key: str = ""
    search_allow_network: bool = False
    search_timeout_seconds: float = 8.0
    search_max_results_default: int = 8
    search_retry_attempts: int = 1
    search_retry_backoff_seconds: float = 0.5
    search_fallback_to_mock: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_prefix="CSL_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
