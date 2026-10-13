from datetime import UTC, datetime
from email.utils import parsedate_to_datetime

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr, field_validator


class ConnectorError(Exception):
    """Classified errors carry no original exception, URL, body or credentials."""

    def __init__(self, code: str, *, transient=False, retry_after=0):
        super().__init__(code)
        self.code, self.transient, self.retry_after = code, transient, retry_after


class SourceJob(BaseModel):
    model_config = ConfigDict(extra="allow", hide_input_in_errors=True)
    id: StrictInt | StrictStr
    title: StrictStr = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def nonblank_title(cls, value):
        if not value.strip():
            raise ValueError("Source title is blank")
        return value


def source_timestamp(value):
    try:
        timestamp = datetime.fromisoformat(value)
        return timestamp.astimezone(UTC) if timestamp.tzinfo is not None else None
    except ValueError, TypeError:
        return None


def retry_seconds(value: str | None) -> int:
    if not value:
        return 0
    try:
        seconds = (
            int(value)
            if value.isdecimal()
            else int((parsedate_to_datetime(value) - datetime.now(UTC)).total_seconds())
        )
        if seconds > 604800:
            raise ConnectorError("SOURCE_PAUSED")
        return max(0, seconds)
    except ValueError, TypeError, OverflowError:
        return 0


def require_success(status, headers):
    if status == 429 or status >= 500:
        raise ConnectorError(
            "SOURCE_RATE_LIMIT" if status == 429 else "SOURCE_UNAVAILABLE",
            transient=True,
            retry_after=retry_seconds(headers.get("retry-after")),
        )
    if not 200 <= status < 300:
        raise ConnectorError("SOURCE_AUTH" if status in (401, 403) else "SOURCE_NOT_FOUND")
