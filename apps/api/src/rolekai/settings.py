"""Validated local settings; database credentials never appear in repr/errors."""

from pathlib import Path
from urllib.parse import urlsplit
from uuid import UUID

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    greenhouse_boards: list[str] = Field(default_factory=list, max_length=100)
    manual_fetch_hosts: list[str] = Field(default_factory=list, max_length=100)
    remotive_queries_per_day: int = Field(default=4, ge=1, le=4)
    current_owner_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    api_access_token: SecretStr | None = Field(default=None, repr=False)
    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[4] / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    database_url: SecretStr = Field(repr=False)
    database_connect_timeout_seconds: int = Field(default=2, ge=1, le=10)

    @field_validator("database_url")
    @classmethod
    def valid_database_url(cls, value: SecretStr) -> SecretStr:
        try:
            parsed = urlsplit(value.get_secret_value())
            valid = parsed.scheme == "postgresql" and parsed.hostname and parsed.path.strip("/")
            # Validate port as well, without putting the input into the error message.
            if parsed.port is not None and not 1 <= parsed.port <= 65535:
                valid = False
        except ValueError:
            valid = False
        if not valid:
            raise ValueError("DATABASE_URL must be a valid postgresql URL with host and database")
        return value
