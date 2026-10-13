"""Shared value types; domains remain independent."""

from datetime import UTC, datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict


def utcnow() -> datetime:
    return datetime.now(UTC)


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True, hide_input_in_errors=True)


class RuleStrength(StrEnum):
    mandatory = "mandatory"
    preferred = "preferred"
    informative = "informative"


class Workplace(StrEnum):
    remote = "remote"
    hybrid = "hybrid"
    onsite = "onsite"
    unknown = "unknown"


class SourceType(StrEnum):
    manual = "manual"
    remotive = "remotive"
    greenhouse = "greenhouse"


class Eligibility(StrEnum):
    eligible = "eligible"
    ineligible = "ineligible"
    unknown = "unknown"
    needs_review = "needs_review"
