---
phase: 01-foundation
plan: '01'
subsystem: infra
tags: [nextjs, typescript, fastapi, pydantic, postgresql, alembic, opentelemetry, quality]
requires: []
provides:
  - Reproducible npm workspace and editable Python 3.14 API package
  - PostgreSQL baseline with independent liveness/readiness and safe OTel
  - Shared local and CI quality commands with negative controls
affects: [02-core-domain]
tech-stack:
  added: [Next.js 16.4.0, React 19.3.0, TypeScript 6.0.3, FastAPI 0.143.0, Pydantic 2.14.1, PostgreSQL 18.4, Psycopg 3.3.6, Alembic 1.20.0, OpenTelemetry 1.45.1]
  patterns: [npm workspaces, src-layout Python package, allowlisted ASGI spans, isolated PostgreSQL tests]
key-files:
  created: [package.json, package-lock.json, apps/web/package.json, apps/api/pyproject.toml, apps/api/requirements.lock, apps/api/src/rolekai/settings.py, apps/api/src/rolekai/main.py, apps/api/src/rolekai/health.py, apps/api/src/rolekai/telemetry.py, apps/api/alembic.ini, compose.yaml, scripts/quality.cjs, .github/workflows/quality.yml, docs/development/SETUP.md]
  modified: [AGENTS.md, .gitignore, tests/development/hooks.test.cjs]
key-decisions:
  - Python 3.14 selected explicitly and checked before gates; no global interpreter changes
  - Official PostgreSQL image pinned by digest and isolated on localhost port 15432
  - No business tables; baseline creates only Alembic version bookkeeping
  - No automatic commits or transition to another phase
requirements-completed: [FND-01, FND-02, FND-03]
actuals:
  tasks: 3
  commits: 0
coverage:
  - id: D1
    description: Reproducible Windows monorepo and Python settings
    requirement: FND-01
    verification:
      - kind: other
        ref: npm.cmd ci and clean Python 3.14 venv install from hashed lock
        status: pass
      - kind: unit
        ref: apps/api/tests/test_settings.py
        status: pass
    human_judgment: false
  - id: D2
    description: PostgreSQL migration, health and redacted request spans
    requirement: FND-02
    verification:
      - kind: integration
        ref: apps/api/tests/integration/test_foundation.py
        status: pass
      - kind: unit
        ref: apps/api/tests/test_health.py and test_telemetry.py
        status: pass
      - kind: other
        ref: Live Uvicorn HTTP 200 liveness/readiness smoke
        status: pass
    human_judgment: false
  - id: D3
    description: Local gates and equivalent configured CI workflow
    requirement: FND-03
    verification:
      - kind: other
        ref: npm.cmd run quality (nine checks, all exit 0)
        status: pass
      - kind: other
        ref: node scripts/test-quality-negative.cjs (type and test rejected)
        status: pass
      - kind: other
        ref: CI YAML parse, official action SHA pins and shared command parity
        status: pass
    human_judgment: true
    rationale: Local behavior verified; remote GitHub CI has not run because no remote/commits were created
completed: 2026-10-13
duration: not measured
status: complete
---

# Phase 1 Plan 1: Foundation Summary

**Next.js/TypeScript shell and FastAPI health API with PostgreSQL baseline, secret-safe settings, OTel correlation and reproducible quality gates.**

## Accomplishments

- Task 1: npm workspace `apps/web`, editable Python package `apps/api`, pinned dependency locks and verified clean installation on Python 3.14.6.
- Task 2: isolated PostgreSQL 18.4, empty Alembic baseline, health endpoints and allowlisted spans. No domain tables or business endpoints.
- Task 3: shared full quality command, Windows/Ubuntu CI definitions, negative controls, web production smoke and Windows setup guide.

## Evidence

- `npm.cmd run quality`: nine checks passed, covering Python version, TypeScript, ESLint, Next build, Ruff, API tests, pip check, continuity and web HTTP smoke.
- API: **14 passed**, including **3 real PostgreSQL integration cases** and OTel redaction/unhandled-error assertions. No warnings in the final API run.
- Agent Continuity: **13 passed**, zero failures/skips on Windows.
- Negative controls: invalid TypeScript rejected with TS2322; intentional Python assertion rejected; temporary files removed and full gates passed afterward.
- `npm.cmd ci`: successful reinstall from lock, lifecycle scripts disabled. Clean venv from explicitly selected Python 3.14: hashed binary dependencies, editable install, 14 tests and pip check passed.
- Alembic upgrade/downgrade/upgrade passed on isolated test database and the newly created empty development database. Only `alembic_version` exists in the baseline.
- Live Uvicorn smoke: `/health/live` and `/health/ready` returned 200, request correlation header present, OpenAPI exposes only those health paths.
- Native GSD artifact verification: 3/3; key link verification: 1/1; consistency: no errors/warnings. Original nine product/architecture hashes unchanged.
- CI configuration parsed and official action versions resolved to commit SHAs. **No remote CI run claimed.**

## Files Created/Modified

- Root `package.json`, `package-lock.json`, `.npmrc`, `.env.example`, `compose.yaml`.
- `apps/web`: package/TS/ESLint configs, minimal layout/page and generated Next env types.
- `apps/api`: package/hashed lock, main/settings/health/telemetry, migration base/template and tests.
- `scripts/quality.cjs`, `smoke-web.cjs`, `test-quality-negative.cjs`, `setup-local-env.cjs`; CI workflow and SETUP guide.
- `.gitignore`, current authorization in AGENTS and the Windows-only hook test's cross-platform skip.
- Native GSD progress/requirements/handoff for **this plan only**.

## Task Commits

None, by explicit user instruction. Git was initially unborn and the previous delivery untracked; no commit, reset, rebase, remote or branch change was performed. Commit-dependent workflow checks were replaced by actual files/tests/native artifact checks, without fabricated hashes.

## Decisions and Deviations

- Supporting settings, lock, baseline, telemetry tests and gate scripts added where necessary for the plan's acceptance criteria.
- Official GSD workflow executed inline: automatic dispatch is restricted in this host adapter. No worktree created from an unborn HEAD and no commit to manufacture one.
- HTTPX2 stable client chosen after inspecting installed Starlette's recommendation; previous HTTPX warning eliminated.
- A clean-venv attempt accidentally selected the host's Python 3.11 alias and failed TLS/dependencies. Diagnosis confirmed PATH divergence; explicit 3.14 succeeded with TLS enabled. The guide and quality gate now validate the interpreter.
- Optional pytest cache disabled after host/sandbox ownership conflict; test semantics unchanged.
- Native progress updated without `state advance-plan`, `phase complete` or auto-chain: active position remains Foundation for review.

## Issues Encountered / Remaining

- ESLint 9.39.4 is deprecated upstream; kept for declared plugin peer compatibility, without forced resolution. Documented tooling debt.
- CLI hook inventory does not load this project's layer under the isolated trust profile. Native interactive Codex trust still needs review; explicit checkpoints work and no bypass/global config edits were used.
- GitHub CI execution is pending a later user-controlled repository/commit setup. Definition/parity and the local full gates are verified.
- Existing GSD health advisories W010/W019 persist; no planning consistency errors. No product code failure remains.

## Next Phase Readiness

Foundation supplies the environment for Core Domain, but **no later plan is authorized or executed** by this delivery. Stop here for review. PostgreSQL is left available locally; temporary web/API smoke servers were stopped. Use SETUP to start/stop normal development services.

## Execution Performance

Source: `.planning/.continuity/foundation-01-quality.json`, final full local gate run from 2026-10-13T17:40:21.068Z to 17:40:51.677Z. This measures child-command elapsed time, including process startup; it is not total implementation time or an isolated pytest benchmark.

| Measurement | Observed duration |
| --- | --- |
| Final full quality run | 30.609 s |
| API test command, including 3 real PostgreSQL cases | 3.831 s |
| Agent Continuity test command | 12.465 s |
| Combined API and continuity test commands | 16.296 s |
| ESLint command | 5.649 s |
| Next production build | 4.528 s |
| TypeScript command | 2.506 s |
| Production web smoke command | 0.818 s |
| Total implementation, install/configuration, retries/corrections, live hooks | Not measured reliably for this increment |

The largest measured command is `node --test tests/development/*.test.cjs` (12.465 s, approximately 41% of the final gate run). ESLint and the production build follow. This identifies command-level cost only; the continuity suite's duration does not measure live hook overhead.

Unquantified rework included host Python PATH divergence, pytest cache ownership and summary self-check parsing. Resolve the selected interpreter explicitly before setup, use the existing cache setting, and keep the final self-check section separate from historical diagnostics. These remedies are already recorded; do not repeat their investigation without new evidence.

For the next authorized increment: reuse valid dependencies and approved architecture; select only tests covering changed behavior during development; run the complete required gate once at the end and repeat only affected checks after subsequent changes. Preserve security/integration/continuity coverage. Record timestamps around installation, necessary retries and native hook invocations when they actually occur; report unavailable durations as unmeasured. No redundant checkpoint or successful test rerun was added for this documentation-only performance follow-up.

## Self-Check: PASSED

All three task acceptance criteria checked against actual commands/tests. Product/architecture docs unchanged, no domain implementation, no automatic Git action, no advancement beyond plan 01-01.
