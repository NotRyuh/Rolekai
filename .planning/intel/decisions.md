# Locked decision references

- Modular monolith, Next.js/TypeScript, FastAPI/Pydantic, PostgreSQL, PostgreSQL worker, OpenTelemetry: `docs/architecture/ARCHITECTURE.md` §§1–8 and `TECH_DECISIONS.md`.
- LangGraph only for intelligent evaluation orchestration: `docs/architecture/AGENT_DESIGN.md` §§1–5; deterministic Hunter/connectors, no autonomous submission.
- P0 sources Remotive/manual URL/Greenhouse; Lever/Ashby P1: `docs/product/DECISIONS.md` D-11, `MVP_BACKLOG.md` E3 and `JOB_HUNTER_SPEC.md` §2.
- Job/Evaluation/Application/Activity distinct: `docs/product/DECISIONS.md` D-07/D-12, `docs/architecture/DATA_MODEL.md` §§1–3.
- Application requires saved Job plus explicit authorization: `docs/architecture/ARCHITECTURE.md` §3 and `API_CONTRACTS.md` §2.
- Tooling-specific: GSD owns `.planning/STATE.md`; technical checkpoints are auxiliary. No product work/commits/branch changes in this delivery (user brief).
