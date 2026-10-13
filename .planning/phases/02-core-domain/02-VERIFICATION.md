---
phase: 02-core-domain
status: passed
verified: 2026-10-13
requirements: [E1-01, E1-02, E1-03, E2-01, E2-02, DOM-01]
---

# Core Domain acceptance verification

1. **Independent states:** Job rejects application/evaluation state; Evaluation has snapshots/version and requirements/evidence; Application uses its own explicit transition graph. Unit and persisted-read cases pass.
2. **Application authorization:** server-configured authenticated owner; spoofed owner fields rejected; foreign resources safely 404; unsaved/unconfirmed Job rejected; strict boolean confirmation; concurrent duplicate results 201/409 with one Application/event.
3. **Immutable/atomic evidence:** composite owner links; original description/provenance retained; immutable snapshot/Activity/transition triggers; domain and event share one real PostgreSQL transaction. Deliberately rejected Activity insert leaves no Application/decision/event changes.

43 API cases pass (15 new real-domain DB cases plus 3 Foundation integration cases), 13 continuity cases pass. Ten local shared quality checks pass; affected API/Ruff rechecked after typed Activity linking. Upgrade/downgrade/upgrade works on dedicated disposable DB; development upgrade succeeds. Drift negative check rejects and preserves changed fixture. Generated types compile. Original nine source hashes unchanged. Native artifact verification 2/2 and key-link 1/1 pass.

Independent review found four functional issues, each reproduced RED and corrected GREEN: timeline pagination, retained reason, enriched decision response and posted-date filter. No Critical/Important finding remains. Async execution is explicitly inactive, not accepted or completed. Remote CI and native interactive hook activation remain unverified; existing tooling advisories unchanged. No commits or later phase started.
