"""Configuración de la aplicación vía variables de entorno (pydantic-settings)."""

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes cargados desde entorno / archivo `.env` en la raíz del repo."""

    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="SubliManager", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    database_url: str = Field(
        default="postgresql+psycopg://sublimanager:sublimanager@localhost:5432/sublimanager",
        alias="DATABASE_URL",
    )
    test_database_url: str | None = Field(default=None, alias="TEST_DATABASE_URL")

    designs_root: str = Field(default="./data/disenos", alias="DESIGNS_ROOT")

    @field_validator("database_url")
    @classmethod
    def validar_url_postgres(cls, valor: str) -> str:
        """Rechaza SQLite u otros motores: PostgreSQL es la BD principal de V1."""
        normalizado = valor.strip().lower()
        if normalizado.startswith("sqlite"):
            raise ValueError(
                "SQLite no está permitido como base de datos principal. "
                "Use postgresql+psycopg://..."
            )
        if not (
            normalizado.startswith("postgresql+")
            or normalizado.startswith("postgresql://")
            or normalizado.startswith("postgres://")
        ):
            raise ValueError(
                "DATABASE_URL debe apuntar a PostgreSQL "
                "(postgresql+psycopg://...)."
            )
        return valor

    @property
    def sqlalchemy_database_url(self) -> str:
        """URL lista para SQLAlchemy (fuerza el driver Psycopg 3 si hace falta)."""
        url = self.database_url
        if url.startswith("postgresql://"):
            return url.replace("postgresql://", "postgresql+psycopg://", 1)
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Singleton de settings (cacheado). Limpiar con get_settings.cache_clear() en tests."""
    return Settings()
