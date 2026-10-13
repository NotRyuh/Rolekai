from datetime import UTC, datetime
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from rolekai.api.contracts import NormalizedJobCandidate
from rolekai.connectors.manual_url import validate_url


def canonical_url(url):
    if url is None:
        return None
    parsed = urlsplit(validate_url(url))
    # Preserve all identity-bearing parameters and ordering; remove only known tracking.
    pairs = [
        (k, v)
        for k, v in parse_qsl(parsed.query, keep_blank_values=True)
        if not k.lower().startswith("utm_") and k.lower() not in ("gclid", "fbclid")
    ]
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(pairs), ""))


def aware_date(value):
    if value is None:
        return None
    try:
        timestamp = datetime.fromisoformat(value)
        # A source-local date without a timezone is retained in payload, not invented as UTC.
        return timestamp.astimezone(UTC) if timestamp.tzinfo is not None else None
    except ValueError, TypeError:
        return None


class Normalizer:
    def __init__(self, owner):
        self.owner = owner

    def normalize(self, raw):
        data = raw.raw_payload
        title = data.get("title") or "Manual opportunity — review required"
        company = data.get("company_name")
        salary = data.get("salary")
        return NormalizedJobCandidate(
            owner_id=self.owner,
            title_raw=title,
            company_display_name=company if isinstance(company, str) and company else None,
            canonical_url=canonical_url(raw.source_url),
            salary=salary if isinstance(salary, str) and salary else None,
            posted_at=aware_date(data.get("publication_date")),
            observations=[raw],
        )
