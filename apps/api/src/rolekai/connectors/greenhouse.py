import re

from pydantic import ValidationError

from rolekai.api.contracts import RawObservation
from rolekai.connectors.base import ConnectorError, SourceJob, source_timestamp
from rolekai.connectors.manual_url import fetch_json, safe_text, validate_url
from rolekai.domain import utcnow


class Greenhouse:
    def __init__(self, board, *, known_boards, fetch_json=fetch_json):
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", board) or board not in known_boards:
            raise ValueError("Known Greenhouse board required")
        self.board, self.fetch_json, self.errors = board, fetch_json, []

    def observation(self, item):
        value = SourceJob.model_validate(item)
        if (
            not isinstance(value.id, int)
            or value.id <= 0
            or not isinstance(item.get("content"), str)
        ):
            raise ValueError("Invalid job")
        return RawObservation(
            source="greenhouse",
            external_id=f"{self.board}:{value.id}",
            source_url=validate_url(item["absolute_url"]),
            retrieved_at=utcnow(),
            source_updated_at=source_timestamp(item.get("updated_at")),
            original_description_html=item["content"],
            original_description_text=safe_text(item["content"]),
            raw_payload=item,
        )

    def discover(self, request):
        data = self.fetch_json(
            f"https://boards-api.greenhouse.io/v1/boards/{self.board}/jobs?content=true"
        )
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("jobs"), list)
            or len(data["jobs"]) > 10000
        ):
            raise ConnectorError("SOURCE_SCHEMA")
        rows, self.errors = [], []
        for item in data["jobs"]:
            try:
                rows.append(self.observation(item))
            except ValidationError, KeyError, ValueError, TypeError, ConnectorError:
                self.errors.append(ConnectorError("SOURCE_SCHEMA"))
        return rows

    def fetch_detail(self, ref):
        ident = (ref.external_id or "").removeprefix(self.board + ":")
        if not ident.isdecimal():
            raise ConnectorError("INVALID_BOARD")
        item = self.fetch_json(
            f"https://boards-api.greenhouse.io/v1/boards/{self.board}/jobs/{ident}?content=true"
        )
        try:
            if str(item.get("id")) != ident:
                raise ValueError("Detail identity mismatch")
            return self.observation(item)
        except ValidationError, KeyError, ValueError, TypeError:
            raise ConnectorError("SOURCE_SCHEMA") from None
