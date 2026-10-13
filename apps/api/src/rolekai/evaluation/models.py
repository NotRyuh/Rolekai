from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from rolekai.domain import DomainModel, RuleStrength, utcnow


class EvaluationStatus(StrEnum):
    not_queued = "not_queued"
    queued = "queued"
    evaluating = "evaluating"
    evaluated = "evaluated"
    needs_review = "needs_review"
    failed = "failed"


class EvidenceSpan(DomainModel):
    observation_id: UUID
    quote: str = Field(min_length=1)


class EvaluationItem(DomainModel):
    requirement: str
    classification: str
    priority: RuleStrength
    result: Literal["covered", "missing", "unknown", "conflicting"]
    reason: str
    confidence: float | None = Field(default=None, ge=0, le=1)
    profile_evidence_id: UUID | None = None
    evidence: list[EvidenceSpan] = Field(min_length=1)

    @model_validator(mode="after")
    def only_covered_links_profile_evidence(self):
        if self.profile_evidence_id is not None and self.result != "covered":
            raise ValueError("Only covered items can link profile evidence")
        return self


class Evaluation(DomainModel):
    id: UUID
    owner_id: UUID
    job_id: UUID
    job_snapshot_hash: str = Field(min_length=1)
    profile_snapshot_hash: str = Field(min_length=1)
    status: EvaluationStatus = EvaluationStatus.not_queued
    fit_score_relative: float | None = Field(default=None, ge=0, le=100)
    score_breakdown_json: dict[str, Any] = Field(default_factory=dict)
    summary: str | None = None
    model_config_data: dict[str, Any] = Field(default_factory=dict)
    prompt_version: str
    requirements: list[EvaluationItem] = Field(default_factory=list)
    evidence: list[EvidenceSpan] = Field(default_factory=list)
    unknowns: list[str] = Field(default_factory=list)
    created_at: AwareDatetime = Field(default_factory=utcnow)
    completed_at: AwareDatetime | None = None
