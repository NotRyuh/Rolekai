# 03-01 unblock and independent review — 2026-10-14

## Confirmed CI diagnosis

Run https://github.com/NotRyuh/Rolekai/actions/runs/38594667672 failed in Ubuntu job `foundation`, step `Prove type and test gates reject invalid inputs`, command `node scripts/test-quality-negative.cjs`, enclosing exit 1. Windows passed but did not previously run the negative controls.

Direct Node invocation did not set `npm_execpath`; scripts assumed the Windows adjacent `node_modules/npm/bin/npm-cli.js`. Linux Node installs npm below `../lib/node_modules/npm/bin/npm-cli.js`. Reproduction in the existing network-disabled Node 24.21.0 Linux image confirmed legacy exit 1/MODULE_NOT_FOUND, corrected npm exit 0. This was tooling configuration, not an intentional type/test defect or application failure. Expected intentional exits are TypeScript 2/TS2322 and pytest 1/intentional assertion.

Shared npm resolution now supports npm-run, Windows and Linux installations. Both negative controls require exact intended exit and diagnostic; Windows CI now also runs them. No control was weakened.

## Independent review and fixes

Read-only reviewer `ingestion_acceptance_review` found four functional defects and one security issue. All were reproduced by failing regression assertions and corrected:

- Field provenance paths now point to original payload keys; normalization/date transformations are classified as rules.
- Human provenance/value survives source refresh; contradictory evidence remains a snapshot and review conflict.
- JobSummary preferred source follows the shared approved source priority.
- Provider JSON redirects are rejected before a second GET, preventing application-path/cross-provider access. Manual safe redirects retain their behavior.
- The well-known NAT64 prefix is rejected before transport to prevent translated private/metadata destinations. Deployment-specific network translation remains subject to network egress controls.

Final reviewer verdict: fixes technically acceptable, no new important defects, no Application writes or contract/scope expansion; acceptance remains conditional on full gate and successful remote CI.

## Verification evidence

- Focused connector/security/ingestion PostgreSQL suite: 43 passed.
- Full gate: 86 API tests and 17 continuity/tooling tests passed; all ten checks passed, including OpenAPI/generated TypeScript drift and production web smoke.
- Actual Windows negative controls: TypeScript exit 2/TS2322; pytest exit 1/intentional assertion; wrapper exits 0 and cleans temporary files.
- Linux npm-layout fixtures: 4 passed; actual Linux legacy/corrected npm probe reproduced the root cause without network or installations.
- GSD artifacts 2/2 and key links 1/1; consistency passed.
- Existing regressions preserve owner isolation, rollback/idempotency, worker fencing, separate similar jobs, manual Job decision and Application `applied` state.
- Portable command evidence: `docs/development/INGESTION_UNBLOCK_VERIFICATION.json`.

## Actual CI and close-out

Latest known remote run is still failed. Local fixes have not been committed or pushed; no new remote run exists. User authorization for a concrete commit/push is required to test this revision in GitHub Actions. Do not call CI green based on local tests. A Linux full Python gate has not been run locally with the Windows venv.

Publication update: user explicitly authorized one commit and push of the reviewed patch and handoff to `master`. New CI success remains pending; this authorization does not advance the plan or permit further automatic commits.

03-01 remains incomplete (2/6 plans complete). Do not create a completion SUMMARY, mark its five requirements complete or start 04-01 until CI success is evidenced. After authorized publication, inspect both jobs and negative controls; then create SUMMARY and perform native GSD acceptance/progress/handoff. No branch change is needed.

## Execution Performance

Full successful gate: 37.946 s process wall time (internal checks 37.878 s); API 13.707 s, continuity/tooling 11.798 s, build 4.018 s, lint 3.044 s. No installation/configuration commands. Total session and live hook overhead are unmeasured. Timing starts after initial recovery/log reads; the portable report contains exact partial-scope timestamps/commands.

Observed retries: first full gate exposed npm environment leakage in new fixtures (undefined triggered the resolver default); isolated fixtures use explicit null. Another final gate stopped on a missing import-group blank line; corrected that formatting. Expected RED regressions are separately recorded. Two Linux diagnostic invocations failed from shell quoting/probe-path mistakes, then the file-based probe succeeded; these command durations are not in the timed report. No architectural retries or dependency reinstalls.

Largest costs were API and continuity startup/integration checks. Next increment: run npm-layout fixtures under npm context, run Ruff before the full gate after Python edits, use file-based cross-platform diagnostics, reuse installed dependencies and keep only one final gate after targeted corrections. Reviewer tool calls measured 0.508 s and 0.159 s; full review duration was not measured.
