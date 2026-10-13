from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, Field

from rolekai.domain import DomainModel


class ActivityEvent(DomainModel):
    model_config = {**DomainModel.model_config, "frozen": True}
    id: UUID
    owner_id: UUID
    subject_type: Literal["job", "application", "profile", "evidence", "evaluation"]
    subject_id: UUID
    event_type: str
    actor_type: Literal["human", "system"]
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    occurred_at: AwareDatetime
    correlation_id: UUID
