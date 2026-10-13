# Cambios de esta entrega

La carpeta inicial contenía solo los nueve documentos aprobados y no tenía Git. Se inicializó Git sin commits, remotes ni cambios de rama. Los nueve originales se preservaron y verificaron por SHA-256. No hay archivos de producto.

## Archivos nuevos para versionar (55)

- `.claude/settings.json`
- `.codex/config.toml`
- `.codex/hooks.json`
- `.gitignore`
- `.planning/HANDOFF.json`
- `.planning/INGEST-CONFLICTS.md`
- `.planning/PROJECT.md`
- `.planning/REQUIREMENTS.md`
- `.planning/ROADMAP.md`
- `.planning/STATE.md`
- `.planning/config.json`
- `.planning/ingest-manifest.yaml`
- `.planning/intel/SYNTHESIS.md`
- `.planning/intel/classifications/AGENT-DESIGN-153547f7.json`
- `.planning/intel/classifications/API-CONTRACTS-cb35c65e.json`
- `.planning/intel/classifications/ARCHITECTURE-35e17173.json`
- `.planning/intel/classifications/DATA-MODEL-3143666e.json`
- `.planning/intel/classifications/DECISIONS-be7f7ba5.json`
- `.planning/intel/classifications/JOB-HUNTER-SPEC-f0beb226.json`
- `.planning/intel/classifications/MVP-BACKLOG-65351716.json`
- `.planning/intel/classifications/PRD-e31c6c3a.json`
- `.planning/intel/classifications/TECH-DECISIONS-7ec10e8a.json`
- `.planning/intel/constraints.md`
- `.planning/intel/context.md`
- `.planning/intel/decisions.md`
- `.planning/intel/requirements.md`
- `.planning/intel/sources.json`
- `.planning/phases/01-foundation/.continue-here.md`
- `.planning/phases/01-foundation/01-01-PLAN.md`
- `.planning/phases/02-core-domain/02-01-PLAN.md`
- `.planning/phases/03-job-ingestion/03-01-PLAN.md`
- `.planning/phases/04-job-intelligence/04-01-PLAN.md`
- `.planning/phases/05-dashboard/05-01-PLAN.md`
- `.planning/phases/06-end-to-end-validation/06-01-PLAN.md`
- `.tools/package-lock.json`
- `.tools/package.json`
- `AGENTS.md`
- `CLAUDE.md`
- `docs/development/AGENT_CONTINUITY.md`
- `docs/development/CHANGES.md`
- `docs/development/GSD_PROVENANCE.json`
- `docs/development/HOOK_BENCHMARK.json`
- `docs/development/INTEGRATION_PLAN.md`
- `docs/development/RUNTIME_VERIFICATION.json`
- `docs/development/VERIFICATION.json`
- `scripts/agent-continuity.cjs`
- `scripts/benchmark-hooks.cjs`
- `scripts/claude-context.cjs`
- `scripts/configure-agents.cjs`
- `scripts/gsd-local-home.cjs`
- `scripts/install-gsd.cjs`
- `scripts/probe-runtimes.cjs`
- `scripts/verify-environment.cjs`
- `tests/development/continuity.test.cjs`
- `tests/development/hooks.test.cjs`

## Configuraciones y assets locales

Versionables: `.claude/settings.json`, `.codex/config.toml`, `.codex/hooks.json`, `.planning/config.json`, `.tools/package.json` y lock. Instrucciones compartidas AGENTS/CLAUDE.

Generados/ignorados: `.claude/commands`, `.claude/agents`, `.claude/gsd-core`, `.claude/hooks`, `.codex/skills`, `.codex/agents`, `.codex/gsd-core`, `.codex/hooks`, node_modules, tarball auditado, home confinado y `.planning/.continuity`. Settings local vacío para evitar duplicación. El detalle de exclusiones está en `.gitignore`.

No se cambiaron configuraciones globales de seguridad de Codex/Claude ni la política de PowerShell. La caché normal de npm se utilizó al descargar paquetes.
