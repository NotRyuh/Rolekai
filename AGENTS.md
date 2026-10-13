# Rolekai development

Product and architecture authority: `docs/product/` and `docs/architecture/`.
GSD shared development state: `.planning/STATE.md`; roadmap/requirements/plans under `.planning/`. Native `HANDOFF.json` and `.continue-here.md` hold semantic handoff. Do not create a second task/state database or store prompts/transcripts/secrets in continuity artifacts.

## Starting and continuing

1. Start from this repository root; read `.planning/STATE.md` first.
2. Run `node scripts/agent-continuity.cjs resume --runtime codex --session <stable-session-id>` (Claude: `--runtime claude`). Read only the referenced active plan/handoff, inspect Git and validate actual work before editing.
3. Use installed GSD commands. Codex: `$gsd-progress`, `$gsd-pause-work`, `$gsd-resume-work`, `$gsd-plan-phase`. Claude: `/gsd-progress`, `/gsd-pause-work`, `/gsd-resume-work`, `/gsd-plan-phase`.
4. For GSD state mutations use `node scripts/agent-continuity.cjs gsd --runtime <runtime> --session <id> -- state update Status "In progress"` and the same wrapper for supported state/complete-todo operations. It rejects stale observations. Re-run resume, review differences and retry intentionally. Native atomic locks serialize writes; they cannot detect stale intent by themselves.
5. Semantic handoff is a native GSD pause operation, never an automatic hook. Serialize direct artifact edits: one semantic writer at a time, re-read immediately before editing, do not edit shared planning concurrently. Direct GSD/direct file writes bypass the optional optimistic guard.
6. Short explicit task capture: `node scripts/agent-continuity.cjs task --session <id> --title "Short task" --phase 1 --next "Concrete action"`. Captures a native GSD todo. Active work is the phase/plan/task in STATE and native handoff; completion is native `todo complete <filename>`; blocking/progress uses STATE and PLAN/SUMMARY. No user-message parsing.

## Current authorization and safety

Foundation and Core Domain are approved. The user authorized only Job Ingestion `03-01-PLAN.md`: manual URL, Remotive and known Greenhouse boards, normalization/exact dedupe, asynchronous import persistence and PostgreSQL worker. Lever, Ashby, evaluator and Dashboard execution remain outside scope. The user's later explicit request authorizes a checkpoint commit and upload to the private NotRyuh/Rolekai repository with a handoff for another machine; it supersedes the previous no-commit restriction for that transfer only. Preserve all previous changes and do not discard/reset staging. No other automatic commits, branches, resets, rebases, `/clear`, security bypasses or session restarts. `planning.commit_docs=false` still applies to native GSD automatic documentation commits.

Hooks are local and deterministic. Codex requires review/trust of new hook definitions in `/hooks`; never bypass it. Install/update procedure and verification limits: `docs/development/AGENT_CONTINUITY.md`.

## Execution efficiency and performance

Recover existing GSD and Agent Continuity state. Read the active plan, project state and relevant files only; expand documentation reads for a specific dependency. Reuse approved research/architecture and valid installed dependencies. Run focused checks during development and all required final gates. Repeat successful commands only for a documented change, failure or unresolved concern. Use native continuity without redundant checkpoints. Diagnose causes before attempting alternative fixes. Preserve every required security and quality validation.

Every execution summary and final report must include **Execution Performance**: reliable total duration, installation/configuration time, test time, retry/correction time and hook time where measured; costly commands, observed bottlenecks and concrete recommendations for the next increment. Identify the measurement source and scope. Mark unavailable metrics as unmeasured; never infer reasoning/tool usage or full-session duration from partial logs. These rules do not authorize additional plans, commits or branch changes.
