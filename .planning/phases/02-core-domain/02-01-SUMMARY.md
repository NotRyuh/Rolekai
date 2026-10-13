---
phase: 02-core-domain
plan: '01'
subsystem: domain
tags: [pydantic, postgresql, sqlalchemy, alembic, ownership, openapi, typescript]
requires:
  - phase: 01-foundation
    provides: Verified API/web skeleton, PostgreSQL and shared quality gates
provides:
  - Owner-scoped typed domains, immutable snapshots and versioned evaluation data
  - Confirmed manual Application services with atomic Activity and transition records
  - Stable deterministic OpenAPI and generated TypeScript with mandatory drift gate
affects: [03-job-ingestion, 04-job-intelligence, 05-dashboard]
tech-stack:
  added: []
  patterns: [composite owner foreign keys, append-only database triggers, row-lock serialization, local bearer identity, timestamp UUID cursors]
key-files:
  created: [apps/api/src/rolekai/domain.py, apps/api/src/rolekai/schema_v2.py, apps/api/src/rolekai/persistence.py, apps/api/src/rolekai/profile/models.py, apps/api/src/rolekai/jobs/models.py, apps/api/src/rolekai/evaluation/models.py, apps/api/src/rolekai/applications/models.py, apps/api/src/rolekai/applications/service.py, apps/api/src/rolekai/activity/models.py, apps/api/src/rolekai/api/contracts.py, apps/api/src/rolekai/api/routes.py, apps/api/src/rolekai/api/errors.py, apps/api/migrations/versions/0002_domains.py, apps/api/tests/test_domain.py, apps/api/tests/test_contracts.py, apps/api/tests/integration/test_domain_transactions.py, packages/contracts/openapi.json, packages/contracts/api-types.ts, scripts/openapi_artifacts.py, scripts/export-openapi.py, scripts/check-openapi.py, scripts/contracts.cjs, apps/web/src/contracts.ts]
  modified: [AGENTS.md, apps/api/src/rolekai/main.py, apps/api/src/rolekai/settings.py, apps/api/migrations/env.py, apps/api/tests/test_health.py, apps/api/tests/integration/test_foundation.py, package.json, scripts/quality.cjs, scripts/setup-local-env.cjs, .env.example, .github/workflows/quality.yml, docs/development/SETUP.md]
key-decisions:
  - Reuse valid dependency locks and interpreters; no installation needed
  - Owner comes from server configuration after local bearer authentication, never a request owner field
  - Persist one Application per owner and Job in P0; no row represents not_applied
  - Async endpoints publish future contracts but return safe inactive 503 without fake runs
  - Independent final review and four behavioral regressions before final acceptance
requirements-completed: [E1-01, E1-02, E1-03, E2-01, E2-02, DOM-01]
duration: not measured for full turn
completed: 2026-10-13
actuals:
  tasks: 3
  commits: 0
  instrumented_implementation_seconds: 1318.024
status: complete
---

# Core Domain 02-01 Summary

**Typed owner-scoped profile, Job, Evaluation, Application and Activity with real PostgreSQL constraints, explicit manual decisions and stable frontend contracts.**

## Implementation

- Search Profile keeps roles, Mexico/remote defaults, mandatory/preferred/informative rules and technology preferences. Evidence requires user-written text, source and date. Models perform no scoring, connector or LLM effects.
- Jobs retain unknown salary/date/country as null and never own application/evaluation status. Immutable source observations preserve original HTML/text/payload and field provenance. Owner-scoped URL/snapshot identity and composite foreign keys prevent cross-owner references.
- Revision `0002_domains` adds UUID/timestamptz/JSONB domain persistence, independent-state checks, indexes and triggers rejecting observation/Activity/transition edits or deletes. Frozen `schema_v2.py` anchors historical migration behavior.
- Server-configured owner plus local bearer token protects domain routes without registration. Safe 404 hides foreign resources; validation/dependency errors use redacted details and correlation IDs. Health remains available.
- Profile/evidence changes, Job decisions and manual Applications write Activity in the same transaction. Saved Job and strict confirmation are mandatory. Explicit transition graph, row locks and uniqueness handle duplicate/concurrent requests; real event-insert failure rolls back both domain write and event. Decision reasons are retained; unchanged decisions create no duplicate event.
- Lists use resource-specific chronological timestamp/UUID cursors and max limit 100. Job posted-date filters are explicit; null dates remain unknown. Evaluation reads preserve stored requirements, linked evidence spans and version hashes without changing Applications.
- `/api/v1` DTOs and validated internal Connector/Normalizer/Deduplication interfaces are published. ImportAccepted uses `run_id`. Async 202 response contracts remain inactive with safe 503 until separately authorized ingestion/evaluator phases. Owner/key/intent retry semantics are specified, not falsely claimed implemented.
- Sorted UTF-8 OpenAPI and dependency-free TypeScript components/paths are generated and checked without rewriting snapshots. Frontend compilation consumes generated types. Contract drift is mandatory in local and CI quality; no deployment/Git action.

## Evidence and acceptance

- E1-01/E1-03: profile unit/default/rule tests plus real persisted profile/preferences service.
- E1-02: dated/source evidence validation and owner-scoped audited 201 creation.
- E2-01/E2-02: unknown fields, retained original descriptions/provenance, owner identity, immutable models/DB records and enriched details.
- DOM-01: independent states, authorization/spoof rejection, saved/confirmed manual creation, 409 conflicts, concurrent duplicate serialization, transitions, atomic rollback and append-only Activity.
- Final full quality: **10 checks approved**, including TypeScript, ESLint, production build, Ruff, OpenAPI/TS drift, pip check, API, continuity and production web smoke.
- **43 API tests approved**, including **15 Core Domain PostgreSQL cases** and the **3 Foundation integration cases** on separate databases. **13 Agent Continuity tests approved**. Final API/Ruff recheck after typed Activity wiring also approved.
- Initial full gate approved 39 API cases; subsequent independent review led to four new regression cases, each RED→GREEN, and a justified final full gate rerun. No Critical or Important finding remains.
- Upgrade/downgrade/upgrade tested on `rolekai_domain_test`; Foundation baseline remains isolated on `rolekai_foundation_test`. Development database upgraded to `0002_domains` without downgrade or data reset.
- Deliberately changed contract snapshot was rejected without rewriting it. Generated types compile; CI uses the same mandatory contract gate.
- Original nine approved product/architecture source hashes unchanged. GSD artifacts 2/2 and key-link 1/1 approved. Summary/consistency/progress checked during close-out.

## Decisions, errors and review

No commits, branches, reset/rebase, dependency reinstall or later plan execution. Git remains unborn master with prior files already untracked. GSD runs inline; an independent read-only reviewer performs the final review required by the execution skill.

Rulings and costs: work in place because creating an initial commit for a worktree violates user scope (cost: less Git isolation); scope source identity by owner/content hash to preserve immutable refresh history (cost: subsequent dedupe must explicitly handle refreshed snapshots); use no Application row for not_applied and retain one row per owner/Job in P0 (cost: reapplication history requires a later migration); publish inactive async routes instead of fictitious queued work (cost: no import/evaluation execution until future authorization); add a dotted-import pattern to the existing GSD key-link metadata because its default searches a literal filesystem path in Python source (cost: static evidence alone is insufficient, so transaction integration tests remain required). Task scope and approved architecture were not changed.

Diagnosed corrections: Windows command-path normalization in auxiliary timing helper; native STATE alias/optimistic-guard mismatches; fixture DSN driver normalization and secret-safe representation; FastAPI pagination parameter flattening; Ruff formatting/imports; strict confirmation/null-status and blank-profile validation; complete evaluation item/span reads. The independent review found chronology and discarded reasons; response defaults/date-filter gaps were regraded functional because they mislead callers. Four focused regressions were written before fixes. No deferred code-review minors remain.

## Pending limits

- Interactive Codex project-hook trust remains unverified under the isolated CLI profile; no bypass or global security edits. Native continuity is saved explicitly.
- Remote GitHub CI has not run: no remote/commits authorized. Local shared commands passed. Existing ESLint 9 deprecation and GSD W010/W019 advisories persist.
- Local single-user bearer identity is not hosted registration/authentication. Async persistence/idempotency execution, source fetching, eligibility/evaluator execution and dashboard are subsequent plans.
- PostgreSQL remains available on loopback port 15432. Domain test fixtures use only their dedicated database; development setup instructions are in SETUP.

## Execution Performance

Source: auxiliary `core-domain-02-performance.json` and `core-domain-02-quality.json` under `.planning/.continuity`. Durations include child-process startup. Instrumentation began after initial state/dependency reads and ended at implementation verification before handoff; full turn duration is unavailable.

| Measurement | Observed time |
| --- | --- |
| Instrumented implementation interval | 21 min 58.024 s |
| Recorded commands, cumulative | 103.828 s |
| Installation | No installations performed |
| Timed configuration commands | 3.650 s (partial; uninstrumented configuration excluded) |
| Focused development test commands, including expected RED runs | 21.330 s |
| Explicit correction retest commands | 3.776 s (code-edit/diagnostic time not measured separately) |
| Final full quality run | 32.534 s |
| API test command in final full gate | 8.593 s |
| Continuity test command in final full gate | 11.257 s |
| Next production build | 3.918 s |
| ESLint | 3.194 s |
| Contract check through npm wrapper | 1.487 s |
| Live hooks, reasoning, full review duration | Not measured |

These rows have overlapping scopes and must not be added into a fictitious total. Two full gate runs were justified by new review fixes; only affected API/Ruff checks were repeated for subsequent Activity wiring. Timing does not estimate thinking or attribute uninstrumented wall time to tools.

The largest measured final commands are continuity (~35%) and API (~26%). Next increment: reuse locks/venv and approved definitions, begin with targeted ingestion fixtures, preserve the full security/transaction/continuity/drift gate at acceptance, use explicit Python paths and safe fixture values, keep FastAPI list query parameters explicit, and include chronology/reason/summary regressions when changing related routes. Measure configuration and necessary rework as they occur; do not reinstall or repeat earlier successful research.

## Stop and handoff

All three tasks in 02-01 are complete. GSD requirements, roadmap, STATE and native handoff are updated for **this plan only**; active phase remains 2 for review. Do not start `03-01` without a separate instruction. No automatic commit.

## Self-Check: PASSED

All three task criteria approved against actual commands and real database behavior. Original source hashes preserved; execution scope respected; native continuation saved.
