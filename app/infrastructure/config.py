import secrets

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_DEV_SECRET = "dev-only-secret-key-change-in-production-32x"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="Ikano Work Sample", alias="APP_NAME")
    app_env: str = Field(default="local", alias="APP_ENV")
    debug: bool = Field(default=False, alias="DEBUG")

    # Must be overridden in production via SECRET_KEY env var.
    secret_key: str = Field(default=_DEV_SECRET, alias="SECRET_KEY")

    db_host: str = Field(default="localhost", alias="DB_HOST")
    db_port: int = Field(default=5432, alias="DB_PORT")
    db_name: str = Field(default="ikano", alias="DB_NAME")
    db_user: str = Field(default="ikano", alias="DB_USER")
    db_password: str = Field(default="ikano", alias="DB_PASSWORD")

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if len(value) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        return value

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+psycopg://{self.db_user}:{self.db_password}@"
            f"{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @staticmethod
    def generate_secret_key() -> str:
        return secrets.token_urlsafe(48)


settings = Settings()
