from datetime import UTC, date, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError


def test_user_profile_preserves_rules_technology_preferences_and_mexico_defaults():
    from rolekai.profile.models import SearchProfile

    profile = SearchProfile(titles=["AI Engineer"], technologies=[{"value": "Python"}])
    assert profile.residence_country == "MX"
    assert profile.workplace.value == "remote"
    assert profile.location_strength.value == "mandatory"
    assert profile.technologies[0].strength.value == "preferred"
    for strength in ("mandatory", "preferred", "informative"):
        assert (
            SearchProfile(titles=["Engineer"], title_strength=strength).title_strength == strength
        )
    with pytest.raises(ValidationError):
        SearchProfile(titles=[])
    with pytest.raises(ValidationError):
        SearchProfile(titles=["Engineer"], title_strength="invented")


def test_evidence_requires_source_date_and_distinguishes_user_evidence_from_inference():
    from rolekai.profile.models import EvidenceCreate

    item = EvidenceCreate(
        text="Built a service", source="Portfolio", evidence_date=date(2026, 1, 1)
    )
    assert item.kind == "user_written"
    with pytest.raises(ValidationError):
        EvidenceCreate(text="Built a service", source="Portfolio")
    with pytest.raises(ValidationError):
        EvidenceCreate(
            text="Invented expertise", source="Model", evidence_date=date.today(), kind="llm"
        )


def test_job_unknowns_stay_null_and_independent_states_cannot_be_attached():
    from rolekai.jobs.models import Job

    data = {"id": uuid4(), "owner_id": uuid4(), "title_raw": "Engineer"}
    job = Job(**data)
    assert (job.salary, job.posted_at, job.country) == (None, None, None)
    assert job.remote_eligibility == "unknown"
    for field in ("application_status", "evaluation_status"):
        with pytest.raises(ValidationError):
            Job(**data, **{field: "applied"})


def test_observations_and_activity_are_immutable_and_keep_original_content():
    from rolekai.activity.models import ActivityEvent
    from rolekai.jobs.models import SourceObservation

    observation = SourceObservation(
        id=uuid4(),
        owner_id=uuid4(),
        job_id=uuid4(),
        source_type="manual",
        source_url="https://example.com/job",
        retrieved_at=datetime.now(UTC),
        content_hash="abc",
        original_description_text="Original",
        parser_version="manual-v1",
    )
    with pytest.raises(ValidationError):
        observation.original_description_text = "Rewritten"
    event = ActivityEvent(
        id=uuid4(),
        owner_id=uuid4(),
        subject_type="job",
        subject_id=uuid4(),
        event_type="job.saved",
        actor_type="human",
        occurred_at=datetime.now(UTC),
        correlation_id=uuid4(),
    )
    with pytest.raises(ValidationError):
        event.event_type = "application.applied"


def test_evaluation_is_versioned_and_does_not_carry_application_state():
    from rolekai.evaluation.models import Evaluation

    data = {
        "id": uuid4(),
        "owner_id": uuid4(),
        "job_id": uuid4(),
        "job_snapshot_hash": "job-v1",
        "profile_snapshot_hash": "profile-v1",
        "prompt_version": "v1",
        "model_config_data": {},
    }
    evaluation = Evaluation(**data)
    assert evaluation.status == "not_queued"
    assert evaluation.fit_score_relative is None
    with pytest.raises(ValidationError):
        Evaluation(**data, application_status="applied")


def test_timezone_less_source_timestamp_is_rejected():
    from rolekai.jobs.models import SourceObservation

    with pytest.raises(ValidationError):
        SourceObservation(
            id=uuid4(),
            owner_id=uuid4(),
            job_id=uuid4(),
            source_type="manual",
            retrieved_at=datetime(2026, 1, 1),
            content_hash="abc",
            parser_version="v1",
        )


def test_confirmation_requires_a_real_boolean_and_null_status_is_invalid():
    from rolekai.applications.models import ApplicationCreate, ApplicationPatch

    for value in ("true", "yes", 1):
        with pytest.raises(ValidationError):
            ApplicationCreate(confirmed=value)
    with pytest.raises(ValidationError):
        ApplicationPatch(status=None, confirmed=True)


def test_profile_rejects_blank_titles_and_technologies():
    from rolekai.profile.models import SearchProfile

    with pytest.raises(ValidationError):
        SearchProfile(titles=["  "])
    with pytest.raises(ValidationError):
        SearchProfile(titles=["Engineer"], technologies=[{"value": "  "}])


def test_evaluation_items_require_source_spans_and_only_covered_can_link_profile():
    from rolekai.evaluation.models import EvaluationItem

    data = {
        "requirement": "Python",
        "classification": "skill",
        "priority": "preferred",
        "result": "unknown",
        "reason": "No evidence",
        "evidence": [{"observation_id": uuid4(), "quote": "Python required"}],
    }
    assert EvaluationItem(**data).result == "unknown"
    with pytest.raises(ValidationError):
        EvaluationItem(**data, profile_evidence_id=uuid4())
    with pytest.raises(ValidationError):
        EvaluationItem(**{**data, "evidence": []})
