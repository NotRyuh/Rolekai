from enum import StrEnum
from uuid import UUID

from pydantic import AwareDatetime, Field, StrictBool, model_validator

from rolekai.domain import DomainModel, utcnow


class ApplicationStatus(StrEnum):
    preparing = "preparing"
    applied = "applied"
    interviewing = "interviewing"
    offer = "offer"
    rejected = "rejected"
    withdrawn = "withdrawn"
    closed_unknown = "closed_unknown"


class ApplicationCreate(DomainModel):
    confirmed: StrictBool
    status: ApplicationStatus = ApplicationStatus.preparing
    applied_at: AwareDatetime | None = None
    channel: str | None = Field(default=None, max_length=200)
    application_url: str | None = Field(default=None, max_length=2000)
    notes: str | None = Field(default=None, max_length=10000)


class ApplicationPatch(DomainModel):
    confirmed: StrictBool = False
    status: ApplicationStatus | None = None
    applied_at: AwareDatetime | None = None
    channel: str | None = Field(default=None, max_length=200)
    notes: str | None = Field(default=None, max_length=10000)

    @model_validator(mode="after")
    def status_cannot_be_cleared(self):
        if "status" in self.model_fields_set and self.status is None:
            raise ValueError("Application status cannot be null")
        return self


class Application(DomainModel):
    id: UUID
    owner_id: UUID
    job_id: UUID
    status: ApplicationStatus
    applied_at: AwareDatetime | None = None
    channel: str | None = None
    application_url: str | None = None
    notes: str | None = None
    created_at: AwareDatetime = Field(default_factory=utcnow)
    updated_at: AwareDatetime = Field(default_factory=utcnow)
