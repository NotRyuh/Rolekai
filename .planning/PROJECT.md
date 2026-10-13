# Rolekai

## What This Is

An auditable career intelligence tool for a candidate resident in Mexico. Product and architecture authorities are the nine sources in `ingest-manifest.yaml`; consult them as needed, not all at session startup.

## Core Value

Discover/import a remote job, understand geographic eligibility and evidence-backed fit, save it, and explicitly record a manual application without automatic submission.

## Requirements

### Validated

- Approved product and modular-monolith architecture documents. Validation here means design approval, not implemented software.

### Active

- [ ] P0 native requirements/roadmap/phase plans. No product requirement is complete yet.

### Out of Scope

- Lever/Ashby activation, expanded Overview/history/CV Studio: P1.
- Tailoring, Gmail, scheduling, automatic Application Monitor: P2.
- Microservices, Redis/Temporal, vector store and multiuser product implementation.
- Automatic application submission at any P0 step.

## Context

Ingest evidence: `.planning/intel/SYNTHESIS.md` and `sources.json`.
Operational integration: `docs/development/AGENT_CONTINUITY.md`.

## Constraints

- Next.js + TypeScript; FastAPI + Pydantic; PostgreSQL worker; OTel base.
- LangGraph scoped to evaluator; domain persistence stays PostgreSQL.
- Human confirmation for sensitive actions, owner isolation, source evidence and idempotency.
- This delivery stops at planning. No commits or branch changes.

## Key Decisions

| Decision | Rationale | Outcome |
| --- | --- | --- |
| Modular monolith and separate domains | Approved architecture §§1–2; DATA_MODEL | Locked |
| Remotive/manual URL/Greenhouse P0 | DECISIONS D-11 | Locked |
| Saved Job + explicit Application authorization | ARCHITECTURE §3/API_CONTRACTS | Locked |
| LangGraph only for intelligent evaluation | AGENT_DESIGN | Locked |
| GSD shared state; auxiliary technical snapshots | User brief | Implemented tooling; runtime trust caveat documented |
