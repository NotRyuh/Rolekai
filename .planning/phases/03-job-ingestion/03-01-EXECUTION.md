# Job Ingestion 03-01 execution ledger

User approved Foundation/Core Domain and authorized only this increment. Native GSD execute-phase marks 03-01 runnable; existing Python/Node dependencies valid, reused. Git unborn master, existing delivery staged; index fingerprint saved and preserved. GSD inline execution/TDD; final independent review per execution skill, no execution auto-dispatch.

- [x] Task 1 implementation/tests: three safe deterministic adapters and versioned source fixtures; 24 connector/security cases pass, including a real local HTTP Host/slow-body check. No live provider calls.
- [x] Task 2 implementation/tests: exact owner-scoped dedupe and attributable snapshots, direct-source conflict preservation, similar-role separation and real rollback cases pass.
- [x] Task 3 implementation/tests: async API, bounded retries, global Remotive budget, fenced worker recovery and race/partial retry cases pass; 13 ingestion PostgreSQL cases.
- [ ] Independent review and final native acceptance/summary; paused for explicit user-requested GitHub transfer. Full local gate already passed (80 API + 13 continuity tests, 10 checks).

Ruling: manual arbitrary URL means user-supplied evidence capture, not unauthorized site scraping. Default URL-only/pasted-text capture performs no fetch; fetching requires explicit allowed-host configuration. Every fetch validates and pins all resolved public IPs, bounds redirect/time/size/content and preserves inert originals. Cost if wrong: narrower extraction; never risk SSRF or imply source permission from reachability.
Ruling: add a new migration for ingestion operations/identity; never mutate frozen schema_v2 or discard existing domain data. Existing test databases retain their historical target revisions; ingestion uses another dedicated disposable database.
Ruling: source IDs are namespaced by known board (Greenhouse) and owner. Exact source ID or conservatively canonicalized URL can match; similar roles remain separate, possibly review candidates. Conflicting exact identities are a safe failure/review, never an automatic merge.
Ruling: Remotive shared global request reservation persists before external HTTP, including retries, with at least six-hour spacing at default four/day. Connector owns no domain repositories; composition passes a rate-budget callback. No live API calls; terms documentation checked once from official sources.

Timing is command elapsed/wall time only; initial preflight, live hooks and reasoning time unmeasured. Native continuity overhead will be timed where actually invoked. No reinstallation or redundant checkpoints.

Diagnostics: additional SSRF tests caught numeric/octal/hex loopback forms and credential queries; validation was tightened before fetching. Greenhouse updated timestamp/detail identity validation added. A real HTTP fixture caught default-port handling and HTTPResponse socket ownership after the declared body length; inspected installed http.client source and corrected loop termination, avoiding speculative retries. Slow body is bounded by deadline/watchdog and declared length. Ruff formatting/import corrections completed before full gate.

Review attempt: independent reviewer could not start due runtime usage limit. No findings or approval were obtained. Do not mark requirements/phase complete until review and necessary fixes are performed. Home resume must inspect source priorities, real payload provenance paths, manual correction preservation, URL/DNS/TLS lifecycle, request-field/source validation, lease renewal and verified unavailability behavior. These are review focus areas, not assertions that all are already accepted.

Ruling: add a Python import pattern to existing key-link verification metadata because GSD's default searches for the literal filesystem target path; actual PostgreSQL transaction/retry tests remain the behavioral gate. Cost if wrong: a static link alone cannot prove behavior.
Ruling: the user's later request explicitly authorizes staging/commit/push of this checkpoint to a private NotRyuh/Rolekai repository, preserving the prior staged content. Previous no-commit restriction superseded only for this transfer. Cost if wrong: publication/commit; private destination/account confirmed before upload.

Execution Performance: last full gate 39.445 s; API process 13.114 s, continuity suite process 11.244 s, ESLint 4.855 s, Next build 4.177 s. Source docs verified once; no dependency installs. See portable docs/development/INGESTION_VERIFICATION.json; partial command timings are auxiliary and excluded from Git. Full-turn/independent-review/live-hook duration unavailable.
