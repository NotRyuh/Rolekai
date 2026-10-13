# Execution ledger — Core Domain 02-01

Authorized: next pending plan only; Foundation approved. Git unborn master, no commits or branch changes. Existing dependencies verified by imports/version checks and reused. GSD/Agent Continuity resumed; native execute-phase identifies 02-01 as runnable.

- [x] Task 1: typed domains, migration and ownership/immutability. Six initial domain tests RED→GREEN; three real persistence/migration tests passed. UUID/timestamptz/JSONB and composite foreign keys; frozen DTOs and database triggers.
- [x] Task 2: authorized services and real transaction/rollback fixtures. Five initial service cases GREEN plus stricter confirmation, owner-spoof, pagination, concurrent duplicate and evaluation-read cases. Domain+Activity rollback proved with a real failing trigger.
- [x] Task 3: deterministic contracts, generated TypeScript and drift gate. Five contract cases RED→GREEN; mandatory drift checks both JSON and TS without rewriting. Async 202 schemas published but safe 503 runtime; import/evaluator execution deferred.
- [x] Final full verification, GSD progress and handoff. 43 API/13 continuity cases approved, 10 gates plus affected Python rechecks; original nine docs unchanged; artifacts 2/2, key-link 1/1, SUMMARY and consistency/completeness approved. Six phase requirements complete, 2/6 plans (33%). Native continuation files updated and one final explicit technical checkpoint saved. Stop in phase 2.

Ruling: work in place and execute GSD inline; unborn HEAD prevents worktree without a prohibited commit; installed host adapter restricts automatic execution delegation. No commits or auto-chain.
Ruling: source identity uniqueness includes owner and content hash. Observations are snapshots, so a refreshed payload must coexist with history and different owners must never collide. Approved source/external uniqueness interpreted as owner-scoped identity, not one mutable global observation.
Ruling: no Application row represents not_applied; persisted Application statuses use DATA_MODEL's seven explicit states. Creation/actual status changes require explicit confirmation.
Ruling: async imports/evaluations publish schemas and inactive endpoint declarations only; return safe 503 until their separately authorized phases. No fake queued/complete runs or in-memory product scheduler.

Timing: auxiliary command durations logged under .planning/.continuity; full turn start, reasoning and hook timing unavailable. No redundant dependency install or checkpoint.

Diagnostics: initial timing helper needed an absolute executable path under Windows; native GSD Current Phase aliases were absent in STATE body, so the existing Phase field was used. A stale guard rejected state writes after planning edits and required a deliberate resume. Integration fixture engine URLs needed conversion from SQLAlchemy dialect form to the approved PostgreSQL DSN; SecretStr prevents fixture credentials appearing in failure summaries. Ruff formatting/import fixes completed before gates. Pagination 422 traced to FastAPI publishing a required params object alongside filters; explicit validated query dependency fixed it.

Final review: independent read-only reviewer found no Critical issues; Important chronology and lost decision reasons confirmed. Source/evaluation response defaults and absent promised date filters regraded Important because they can mislead consumers or silently ignore a filter, not merely style issues.
Final: fixed chronology/timestamp cursor — test_activity_timeline_cursor_orders_time_then_uuid_without_skipping_ties RED→GREEN.
Final: fixed decision reason persistence — test_decision_reason_is_retained_in_its_atomic_activity RED→GREEN.
Final: fixed enriched decision response — test_decision_response_preserves_source_and_latest_evaluation RED→GREEN.
Final: fixed published date filtering — test_jobs_posted_date_filter_keeps_unknown_dates_unknown RED→GREEN.
Final: Ruling: deferred asynchronous execution, connector/evaluator/UI and registration remain outside this plan; safe inactive routes are the concrete behavior. Cost if wrong: accepting fake asynchronous work or expanding user scope. Reapplication history remains a later explicit model change.
Initial full gate: 10 checks passed, 39 API tests and 13 continuity tests. Subsequent review fixes justify one final full rerun; no reviewer re-dispatch.
Final full gate: 10 checks passed, 43 API tests and 13 continuity tests. After explicitly validating ActivityEvent before its INSERT, affected full API suite (43 tests) and Ruff passed again; web/continuity/contract gates were not redundantly repeated.
Ruling: add an import pattern to the existing GSD key-link verification metadata only. Without a pattern GSD searches for the literal filesystem target path in Python source, which cannot match a normal dotted import. The approved transaction requirement and task scope are unchanged; real failing-trigger rollback tests provide behavioral evidence. Cost if wrong: a static link check could overstate wiring, so actual PostgreSQL tests remain mandatory.
