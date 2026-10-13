from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field, StringConstraints

from rolekai.domain import DomainModel, RuleStrength, Workplace

Nonblank = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=120)]


class TechnologyPreference(DomainModel):
    value: Nonblank
    strength: RuleStrength = RuleStrength.preferred


class SearchProfile(DomainModel):
    titles: list[Nonblank] = Field(min_length=1, max_length=30)
    title_strength: RuleStrength = RuleStrength.preferred
    residence_country: str = Field(default="MX", pattern=r"^[A-Z]{2}$")
    location_strength: RuleStrength = RuleStrength.mandatory
    workplace: Workplace = Workplace.remote
    workplace_strength: RuleStrength = RuleStrength.mandatory
    technologies: list[TechnologyPreference] = Field(default_factory=list, max_length=100)
    salary_min: float | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, pattern=r"^[A-Z]{3}$")
    languages: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)


class EvidenceCreate(DomainModel):
    text: str = Field(min_length=1, max_length=10000)
    source: str = Field(min_length=1, max_length=2000)
    evidence_date: date
    kind: Literal["user_written"] = "user_written"


class ProfileEvidence(EvidenceCreate):
    id: UUID
    owner_id: UUID
