from sqlalchemy import select

from rolekai.api.contracts import Resolution
from rolekai.connectors.base import ConnectorError
from rolekai.persistence import jobs, observations
from rolekai.workflows.tables import source_identities, url_identities


class DeduplicationService:
    def __init__(self, connection, owner):
        self.connection, self.owner = connection, owner

    def resolve(self, candidate):
        c, owner = self.connection, self.owner
        raw = candidate.observations[0]
        identities = set()
        if raw.external_id is not None:
            identities.update(
                c.scalars(
                    select(source_identities.c.job_id).where(
                        source_identities.c.owner_id == owner,
                        source_identities.c.source == raw.source,
                        source_identities.c.external_id == raw.external_id,
                    )
                )
            )
            identities.update(
                c.scalars(
                    select(observations.c.job_id)
                    .where(
                        observations.c.owner_id == owner,
                        observations.c.source_type == raw.source,
                        observations.c.external_id == raw.external_id,
                    )
                    .distinct()
                )
            )
        if candidate.canonical_url:
            identities.update(
                c.scalars(
                    select(url_identities.c.job_id).where(
                        url_identities.c.owner_id == owner,
                        url_identities.c.url == candidate.canonical_url,
                    )
                )
            )
            identities.update(
                c.scalars(
                    select(jobs.c.id).where(
                        jobs.c.owner_id == owner, jobs.c.canonical_url == candidate.canonical_url
                    )
                )
            )
        if len(identities) > 1:
            raise ConnectorError("IDENTITY_CONFLICT")
        if identities:
            return Resolution(action="Update", job_id=next(iter(identities)))
        normalized = " ".join(candidate.title_raw.casefold().split())
        similar = (
            list(
                c.scalars(
                    select(jobs.c.id).where(
                        jobs.c.owner_id == owner,
                        jobs.c.title_normalized == normalized,
                        jobs.c.company_key == (candidate.company_display_name or "").casefold(),
                    )
                )
            )
            if candidate.company_display_name
            else []
        )
        return Resolution(action="MergeCandidate" if similar else "Create", candidate_ids=similar)
