from urllib.parse import urlencode

from pydantic import ValidationError

from rolekai.api.contracts import RawObservation
from rolekai.connectors.base import ConnectorError, SourceJob
from rolekai.connectors.manual_url import fetch_json, safe_text, validate_url
from rolekai.domain import utcnow


class Remotive:
    def __init__(self, *, fetch_json=fetch_json, reserve=None):
        self.fetch_json, self.reserve = fetch_json, reserve
        self.errors = []

    def discover(self, request):
        if self.reserve is None:
            raise ConnectorError("RATE_BUDGET_REQUIRED")
        self.reserve()
        url = "https://remotive.com/api/remote-jobs"
        if request.query:
            url += "?" + urlencode({"search": request.query})
        data = self.fetch_json(url)
        if (
            not isinstance(data, dict)
            or not isinstance(data.get("jobs"), list)
            or len(data["jobs"]) > 10000
        ):
            raise ConnectorError("SOURCE_SCHEMA")
        rows, self.errors = [], []
        for item in data["jobs"]:
            try:
                value = SourceJob.model_validate(item)
                if not str(value.id).strip() or isinstance(value.id, int) and value.id <= 0:
                    raise ValueError("Invalid identity")
                link = validate_url(item["url"])
                if not isinstance(item.get("description"), str):
                    raise ValueError("Description required")
                rows.append(
                    RawObservation(
                        source="remotive",
                        external_id=str(value.id),
                        source_url=link,
                        retrieved_at=utcnow(),
                        original_description_html=item["description"],
                        original_description_text=safe_text(item["description"]),
                        attribution="Remotive — " + link,
                        raw_payload={**item, "freshness_delay_hours": 24},
                    )
                )
            except ValidationError, KeyError, ValueError, TypeError, ConnectorError:
                self.errors.append(ConnectorError("SOURCE_SCHEMA"))
        return rows

    def fetch_detail(self, ref):
        from uuid import UUID

        from rolekai.api.contracts import DiscoverRequest

        for row in self.discover(DiscoverRequest(owner_id=UUID(int=0), source="remotive")):
            if row.external_id == ref.external_id:
                return row
        raise ConnectorError("SOURCE_NOT_FOUND")
