# Roadmap: Rolekai P0

## Overview

One approved vertical slice: Remotive/manual URL/Greenhouse → immutable observation/Job → evidenced eligibility/Evaluation → Discover/Save → confirmed manual Application. Architecture stays a modular monolith. This is the only product roadmap; Foundation 01-01 and Core Domain 02-01 are complete and all later work awaits separate execution authorization.

## Phases

- [x] **Phase 1: Foundation** - P0.1 monorepo, environment, PostgreSQL, migrations, gates and health. (completed 2026-10-13)
- [x] **Phase 2: Core Domain** - P0.2 profile/evidence, Job/observations, Evaluation, Application, Activity and contracts. (completed 2026-10-13)
- [ ] **Phase 3: Job Ingestion** - P0.3 manual URL, Remotive, Greenhouse, normalization/dedupe/provenance/persistence.
- [ ] **Phase 4: Job Intelligence** - P0.4 Mexico eligibility and evidence-backed versioned evaluations.
- [ ] **Phase 5: Dashboard** - P0.5 Discover/Saved/Applications/minimal Activity/profile.
- [ ] **Phase 6: End-to-End Validation** - P0.6 fixtures, integration, idempotency, real job samples and documentation.

## Phase Details

### Phase 1: Foundation

**Goal**: Reproducible modular monolith skeleton with observable health and PostgreSQL migration/gate foundations.
**Depends on**: Nothing (first phase)
**Requirements**: FND-01, FND-02, FND-03
**Success Criteria**:
  1. Windows setup starts API/web/PostgreSQL from documented commands with no committed secrets.
  2. PostgreSQL readiness detects dependency failure; migration roundtrip works on an empty database.
  3. Local and CI quality gates enforce type/lint/test contracts and OTel redaction.

**Plans**: 1/1 plans complete

Plans:
- [x] 01-01: Environment, migration/health foundations and quality gates.

### Phase 2: Core Domain

**Goal**: Typed, independently stateful domains, profile evidence and ownership/authorization invariants.
**Depends on**: Phase 1
**Requirements**: E1-01, E1-02, E1-03, E2-01, E2-02, DOM-01
**Success Criteria**:
  1. Profile rules/evidence and jobs retain sources/unknowns and owner isolation.
  2. Observations and Activity are immutable; Evaluation and Application states are not fields on Job.
  3. Unsaved/unconfirmed Application requests fail safely; domain changes plus Activity commit atomically.

**Plans**: 1/1 plans complete

Plans:
- [x] 02-01: Domain models, persistence invariants and OpenAPI contracts.

### Phase 3: Job Ingestion

**Goal**: All three authorized P0 sources yield traceable observations/jobs with safe idempotent execution.
**Depends on**: Phase 2
**Requirements**: E3-01, E3-02, E3-03, E4-01, ING-01
**Success Criteria**:
  1. Manual fallback preserves URL/date/text; private-network URL retrieval is blocked.
  2. Remotive attribution/frequency and Greenhouse known-board detail contracts pass fixtures.
  3. Reimport/retry creates no duplicate job; source failure is isolated and provenance remains auditable.

**Plans**: 1 plan

Plans:
- [ ] 03-01: Connector adapters, normalization/dedupe and PostgreSQL worker pipeline.

### Phase 4: Job Intelligence

**Goal**: Geographic filtering and bounded evaluator produce cited, versioned outcomes with abstention.
**Depends on**: Phase 3
**Requirements**: E4-02, E4-03
**Success Criteria**:
  1. Worldwide/LATAM/Mexico, US-only, remote-unspecified and conflicting fixtures produce evidenced distinct outcomes.
  2. Evaluation cites job spans/profile evidence; unknown evidence never becomes invented experience.
  3. Invalid output/failure persists failed/needs_review; a new model/prompt version creates a new Evaluation.

**Plans**: 1 plan

Plans:
- [ ] 04-01: Deterministic eligibility and snapshot-based LangGraph evaluator.

### Phase 5: Dashboard

**Goal**: User can review evidence, save/dismiss and explicitly record a manual application with independent views.
**Depends on**: Phase 4
**Requirements**: E5-01, E5-02, E5-03, UI-01
**Success Criteria**:
  1. Discover/Saved filters and job detail expose original description, provenance and evaluation unknowns.
  2. Save/dismiss never creates Application; confirmation plus saved Job is required for manual tracking.
  3. Applications/minimal Activity/Settings use typed API, accessible controls, sanitized HTML and safe failure states.

**Plans**: 1 plan

Plans:
- [ ] 05-01: Typed dashboard, human decisions and manual tracking.

### Phase 6: End-to-End Validation

**Goal**: Prove the P0 vertical slice against deterministic fixtures, PostgreSQL and authorized real samples.
**Depends on**: Phase 5
**Requirements**: E2E-01
**Success Criteria**:
  1. Unit/integration/API/browser/security/evaluator checks pass with reproducible evidence.
  2. Real samples cover all enabled sources, exact duplicate, Mexico-compatible/incompatible/unknown jobs.
  3. Source limits, operational recovery, retention and user-control limitations are documented; no automatic submission exists.

**Plans**: 1 plan

Plans:
- [ ] 06-01: Acceptance dataset, resilience/security validation and operational documentation.

## Progress

| Phase | Plans Complete | Status | Completed |
| --- | --- | --- | --- |
| 1. Foundation | 1/1 | Complete    | 2026-10-13 |
| 2. Core Domain | 1/1 | Complete    | 2026-10-13 |
| 3. Job Ingestion | 0/1 | In progress; remote CI pending | - |
| 4. Job Intelligence | 0/1 | Not started | - |
| 5. Dashboard | 0/1 | Not started | - |
| 6. End-to-End Validation | 0/1 | Not started | - |
