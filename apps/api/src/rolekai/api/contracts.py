from typing import Any, Literal, Protocol
from uuid import UUID

from pydantic import AwareDatetime, Field

from rolekai.activity.models import ActivityEvent
from rolekai.applications.models import Application
from rolekai.domain import DomainModel, Eligibility, SourceType, Workplace
from rolekai.evaluation.models import Evaluation
from rolekai.jobs.models import DecisionStatus, FieldProvenance, Job, SourceObservation
from rolekai.profile.models import ProfileEvidence


class ErrorDetail(DomainModel):
    code: str
    message: str
    details: list[str] = Field(default_factory=list)
    request_id: UUID


class ErrorResponse(DomainModel):
    error: ErrorDetail


class PageQuery(DomainModel):
    limit: int = Field(default=20, ge=1, le=100)
    cursor: str | None = Field(default=None, max_length=200)


class DecisionChange(DomainModel):
    decision_status: DecisionStatus
    reason: str | None = Field(default=None, max_length=2000)


class EvaluationSummary(DomainModel):
    id: UUID
    status: str
    fit_score_relative: float | None = None


class JobSummary(Job):
    preferred_source: SourceType | None = None
    latest_evaluation: EvaluationSummary | None = None


class JobDetail(JobSummary):
    observations: list[SourceObservation] = Field(default_factory=list)
    provenance: list[FieldProvenance] = Field(default_factory=list)
    evaluations: list[Evaluation] = Field(default_factory=list)
    application: Application | None = None
    merge_candidate_ids: list[UUID] = Field(default_factory=list)


class JobListPage(DomainModel):
    items: list[JobSummary]
    next_cursor: str | None = None


class EvidencePage(DomainModel):
    items: list[ProfileEvidence]
    next_cursor: str | None = None


class ActivityPage(DomainModel):
    items: list[ActivityEvent]
    next_cursor: str | None = None


class ImportRequest(DomainModel):
    query: str | None = Field(default=None, max_length=500)
    url: str | None = Field(default=None, max_length=2000)
    board: str | None = Field(default=None, max_length=200)
    text: str | None = Field(default=None, max_length=100000)


class ImportAccepted(DomainModel):
    run_id: UUID
    status: Literal["queued"] = "queued"
    source: SourceType
    submitted_at: AwareDatetime


class ImportRun(DomainModel):
    run_id: UUID
    status: Literal["queued", "running", "completed", "failed"]
    source: SourceType
    created: int = Field(default=0, ge=0)
    updated: int = Field(default=0, ge=0)
    duplicate: int = Field(default=0, ge=0)
    needs_review: int = Field(default=0, ge=0)
    failed: int = Field(default=0, ge=0)
    errors: list[ErrorDetail] = Field(default_factory=list)
    job_ids: list[UUID] = Field(default_factory=list)


class EvaluationAccepted(DomainModel):
    evaluation_id: UUID
    status: Literal["queued"] = "queued"


class RawObservation(DomainModel):
    source: SourceType
    external_id: str | None = None
    source_url: str | None = None
    retrieved_at: AwareDatetime
    source_updated_at: AwareDatetime | None = None
    raw_payload: dict[str, Any] = Field(default_factory=dict)
    original_description_html: str | None = None
    original_description_text: str | None = None
    attribution: str | None = None


class DiscoverRequest(DomainModel):
    owner_id: UUID
    source: SourceType
    query: str | None = None
    url: str | None = None
    text: str | None = None
    board: str | None = None


class SourceReference(DomainModel):
    source: SourceType
    external_id: str | None = None
    url: str | None = None


class NormalizedJobCandidate(DomainModel):
    owner_id: UUID
    title_raw: str = Field(min_length=1)
    company_display_name: str | None = None
    canonical_url: str | None = None
    salary: str | None = None
    posted_at: AwareDatetime | None = None
    country: str | None = None
    workplace_type: Workplace = Workplace.unknown
    remote_eligibility: Eligibility = Eligibility.unknown
    observations: list[RawObservation] = Field(min_length=1)


class Resolution(DomainModel):
    action: Literal["Create", "Update", "MergeCandidate"]
    job_id: UUID | None = None
    candidate_ids: list[UUID] = Field(default_factory=list)


class Connector(Protocol):
    def discover(self, request: DiscoverRequest) -> list[RawObservation]: ...
    def fetch_detail(self, ref: SourceReference) -> RawObservation: ...


class Normalizer(Protocol):
    def normalize(self, raw: RawObservation) -> NormalizedJobCandidate: ...


class DeduplicationService(Protocol):
    def resolve(self, candidate: NormalizedJobCandidate) -> Resolution: ...


class ImportScheduler(Protocol):
    """Phase 3 must persist (owner, key, intent) and repeat the same run_id.

    A key reused with a different intent returns 409; no side effect is completed
    by returning queued. No implementation is provided in Core Domain.
    """

    def accept(self, owner_id: UUID, key: str, request: ImportRequest) -> ImportAccepted: ...
