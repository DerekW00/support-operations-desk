# Tradeoffs and limits

- PostgreSQL row locks and a durable job table expose ownership and recovery directly. Redis/Celery would add operational dependencies without improving this bounded local workflow.
- Organization-level ingestion locking deliberately trades import concurrency for simple cross-account event-key correctness. Current imports are bounded at 50 tickets; no throughput claim is made.
- Review history is append-only through supported application paths. A database administrator can still alter rows; this is not a tamper-proof or cryptographically signed audit system.
- Source IDs provide traceability, not semantic truth. There is no retrieval-quality or entailment claim. Synthetic source records are not editable through this interface.
- Replies use a finite approved statement library rather than unrestricted prose. Reviewers can correct category and add, remove or reorder up to 12 exact statements; custom wording, even benign wording, is rejected. This intentionally trades expressive flexibility for a demonstrable no-financial-or-resolution-time-commitment contract. Extending the library is a deliberate policy change requiring tests and review, not a model capability.
- Approval records the explicit latest suggestion basis plus its source snapshot. New suggestions always require fresh review; the form replaces old content and marks it unapproved. Existing historical records with no basis are preserved without inferred backfills and require fresh review before editing.
- Guard reservations are admission accounting, not tokens billed. Recorded fixtures have unknown usage. A transport failure may have consumed real provider usage in a future adapter; this implementation never fabricates a number.
- Lease recovery can duplicate an in-flight external call after a crash. Claim tokens fence database publication, not remote provider side effects. The current provider makes no external calls.
- Jobs run synchronously in a small management-command worker, with two attempts and 120 seconds total. Expired work is marked terminal on the next claim scan. The UI stops polling at the deadline even if no worker is available.
- Membership intentionally selects one organization per user. Multi-organization switching, role delegation, SSO, rate limiting and hosted security configuration are not included.
- Approval records a human decision and never sends customer communications. A future send capability would need separate authorization, immutable approved content and external delivery idempotency.
- The optional Compose route is a local development convenience only, binds PostgreSQL to loopback, and uses local trust authentication. Actual verification used a separate private PostgreSQL 16 cluster over a Unix socket, not Docker or SQLite.
