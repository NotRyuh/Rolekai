# Requirements: Rolekai P0

Unchecked items remain unimplemented product work; checked items are backed by their plan summaries and verification. Source acceptance criteria remain authoritative in docs. Technical enablers below operationalize the approved architecture.

## v1 Requirements

### Foundation

- [x] **FND-01**: Monorepo, documented Windows setup, reproducible Node/Python dependencies and environment variables.
- [x] **FND-02**: PostgreSQL, migration upgrade/downgrade smoke checks, liveness/readiness and OTel without sensitive payloads.
- [x] **FND-03**: CI/local quality gates for TypeScript, Python, tests and generated API contracts.

### Domain and profile

- [x] **E1-01**: Configure roles, Mexico residence and modality with mandatory/preferred rules.
- [x] **E1-02**: Record dated professional evidence with source, separating fact from inference.
- [x] **E1-03**: Persist technology preferences for transparent evaluation.
- [x] **E2-01**: Job/detail retains original description, normalized fields, dates and explicit unknowns.
- [x] **E2-02**: Immutable observations and field provenance distinguish human corrections.
- [x] **DOM-01**: Separate Job/Evaluation/Application/Activity contracts; owner isolation; saved Job + explicit Application action; atomic append-only activity.

### Ingestion

- [ ] **E3-01**: Remotive discovery with attribution/link, bounded frequency and classified errors.
- [ ] **E3-02**: Manual URL with recoverable content or pasted-text fallback; URL/date still saved on inaccessible pages.
- [ ] **E3-03**: Known Greenhouse board/URL imports ID/title/location/URL/content without submission endpoints.
- [ ] **E4-01**: Source ID/URL exact dedupe; retry/reimport preserves observations and creates no duplicate job.
- [ ] **ING-01**: PostgreSQL worker claims, idempotency, bounded retries and source isolation; SSRF/HTML defenses; aggregate ImportRun results.

### Intelligence

- [ ] **E4-02**: Mexico/remote eligibility eligible/ineligible/unknown/needs_review with source evidence.
- [ ] **E4-03**: Versioned evaluation separates covered/missing/unknown, cites job/profile evidence, optional relative fit score, no hiring probability.

### Dashboard

- [ ] **E5-01**: Discover filtered by source/title/date/modality/eligibility.
- [ ] **E5-02**: Save/dismiss records activity and never creates Application.
- [ ] **E5-03**: Confirmed manual Application from saved Job with separate status board.
- [ ] **UI-01**: Saved Jobs, minimal Activity and Settings/profile views expose evidence and safe errors.

### End-to-end acceptance

- [ ] **E2E-01**: Unit/integration/OpenAPI/evaluation/security fixtures pass; live authorized source examples satisfy the PRD §11 and MVP DoD, including exact duplicates and eligibility variants; documentation records source limitations.

## Future Requirements

All P1/P2 IDs in `docs/product/MVP_BACKLOG.md` remain deferred. No checkboxes or second roadmap for that backlog here.

## Traceability

| Requirement | Phase | Status |
| --- | --- | --- |
| FND-01 | Phase 1 | Complete |
| FND-02 | Phase 1 | Complete |
| FND-03 | Phase 1 | Complete |
| E1-01 | Phase 2 | Complete |
| E1-02 | Phase 2 | Complete |
| E1-03 | Phase 2 | Complete |
| E2-01 | Phase 2 | Complete |
| E2-02 | Phase 2 | Complete |
| DOM-01 | Phase 2 | Complete |
| E3-01 | Phase 3 | Pending |
| E3-02 | Phase 3 | Pending |
| E3-03 | Phase 3 | Pending |
| E4-01 | Phase 3 | Pending |
| ING-01 | Phase 3 | Pending |
| E4-02 | Phase 4 | Pending |
| E4-03 | Phase 4 | Pending |
| E5-01 | Phase 5 | Pending |
| E5-02 | Phase 5 | Pending |
| E5-03 | Phase 5 | Pending |
| UI-01 | Phase 5 | Pending |
| E2E-01 | Phase 6 | Pending |
