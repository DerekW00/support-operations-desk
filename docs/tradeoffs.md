# Tradeoffs and limits

- PostgreSQL row locks and a durable job table expose ownership and recovery directly. Redis/Celery would add operational dependencies without improving this bounded local workflow.
- Organization-level ingestion locking deliberately trades import concurrency for simple cross-account event-key correctness. Current imports are bounded at 50 tickets; no throughput claim is made.
- Review history is append-only through supported application paths. A database administrator can still alter rows; this is not a tamper-proof or cryptographically signed audit system.
- Source IDs provide traceability, not semantic truth. There is no retrieval-quality or entailment claim. Synthetic source records are not editable through this interface.
- Conservative promise validation can reject benign mentions of refunds or credits. It prevents obvious financial/timing promises but is not a complete natural-language safety classifier. A real provider integration requires stronger structured entitlement contracts and separate validation.
- Guard reservations are admission accounting, not tokens billed. Recorded fixtures have unknown usage. A transport failure may have consumed real provider usage in a future adapter; this implementation never fabricates a number.
- Lease recovery can duplicate an in-flight external call after a crash. Claim tokens fence database publication, not remote provider side effects. The current provider makes no external calls.
- Jobs run synchronously in a small management-command worker, with two attempts and 120 seconds total. Expired work is marked terminal on the next claim scan. The UI stops polling at the deadline even if no worker is available.
- Membership intentionally selects one organization per user. Multi-organization switching, role delegation, SSO, rate limiting and hosted security configuration are not included.
- Approval records a human decision and never sends customer communications. A future send capability would need separate authorization, immutable approved content and external delivery idempotency.
- The optional Compose route is a local development convenience only, binds PostgreSQL to loopback, and uses local trust authentication. Actual verification used a separate private PostgreSQL 16 cluster over a Unix socket, not Docker or SQLite.
