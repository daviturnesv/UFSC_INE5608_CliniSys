from __future__ import annotations

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "CliniSys-Escola API"
    environment: str = "dev"

    # Security
    secret_key: str = "changeme"  # substituir em produção
    access_token_expire_minutes: int = 60
    algorithm: str = "HS256"

    # Database (override via env vars)
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "clinisysschool"

    class Config:
        env_file = ".env"
        env_prefix = "APP_"
        case_sensitive = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
