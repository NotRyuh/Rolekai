from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field

from rolekai.domain import DomainModel, Eligibility, SourceType, Workplace, utcnow


class DecisionStatus(StrEnum):
    inbox = "inbox"
    saved = "saved"
    dismissed = "dismissed"


class DiscoveryStatus(StrEnum):
    new = "new"
    imported = "imported"
    normalized = "normalized"
    duplicate_candidate = "duplicate_candidate"
    merged = "merged"
    archived = "archived"
    unavailable = "unavailable"
    unknown_availability = "unknown_availability"


class Job(DomainModel):
    id: UUID
    owner_id: UUID
    title_raw: str = Field(min_length=1)
    title_normalized: str | None = None
    company_display_name: str | None = None
    company_key: str | None = None
    canonical_url: str | None = None
    apply_url: str | None = None
    workplace_type: Workplace = Workplace.unknown
    remote_eligibility: Eligibility = Eligibility.unknown
    eligibility_reason: str | None = None
    availability_status: Literal["available", "unavailable", "unknown"] = "unknown"
    discovery_status: DiscoveryStatus = DiscoveryStatus.new
    decision_status: DecisionStatus = DecisionStatus.inbox
    salary: str | None = None
    country: str | None = None
    posted_at: AwareDatetime | None = None
    discovered_at: AwareDatetime = Field(default_factory=utcnow)
    last_verified_at: AwareDatetime | None = None
    created_at: AwareDatetime = Field(default_factory=utcnow)
    updated_at: AwareDatetime = Field(default_factory=utcnow)


class SourceObservation(DomainModel):
    model_config = {**DomainModel.model_config, "frozen": True}
    id: UUID
    owner_id: UUID
    job_id: UUID
    import_run_id: UUID | None = None
    source_type: SourceType
    external_id: str | None = None
    source_url: str | None = None
    retrieved_at: AwareDatetime
    source_updated_at: AwareDatetime | None = None
    content_hash: str
    raw_payload_json: dict[str, Any] = Field(default_factory=dict)
    original_description_html: str | None = None
    original_description_text: str | None = None
    attribution: str | None = None
    parser_version: str


class FieldProvenance(DomainModel):
    id: UUID
    job_id: UUID
    observation_id: UUID
    field_name: str
    payload_path: str | None = None
    citation: str | None = None
    provenance_type: Literal["source", "rule", "human", "llm"]
    confidence: float | None = Field(default=None, ge=0, le=1)
