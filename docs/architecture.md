# Architecture

Django 5.2 supplies sessions, CSRF, forms, templates and ORM migrations. PostgreSQL 16 is the only application service. Python 3.12 owns policy, ingestion, revision handling, provider validation, worker execution and evaluation. The interface uses server-rendered HTML/CSS and locally vendored HTMX 2.0.8; no frontend compilation is required.

## Domain

Organization and one active Membership per user resolve tenancy on the server. Account tier and active verified Outage records determine the ticket deadline: standard 24 hours, priority 4 hours, verified outage one hour with escalation. Customer text is untrusted and never enters that decision. SLA is captured at ingestion, rather than silently recalculated if account facts later change.

Ticket stores the original event key, canonical SHA-256 content hash and received policy outcome. Ingestion locks organization then account, preventing duplicate-event races even when concurrent changed payloads name different accounts. Bulk validation/publication is atomic. The database independently enforces organization/event uniqueness.

Source holds tenant-owned synthetic guidance. SuggestionRecord stores a cited fixture reply and publication revision. Review stores actor, category, reply, approval, timestamp, explicit basis-suggestion identity and a source-ID snapshot. Public service paths create history rows without updating existing history. Each suggestion publication and human save advances Ticket.revision while holding its row lock. A stale expected revision raises a conflict, including when a newer suggestion arrived after the form opened. The posted basis must also identify the latest suggestion for this ticket. Reload selects a newer suggestion rather than the old review text, marks it as needing review, and shows its evidence identity. Approval badges apply only to the current content revision and matching basis; older decisions remain visibly historical. Legacy rows without a known basis require fresh review.

## Worker protocol

Job stores state, random claim token, lease, deadline, attempt count, admitted guard reservations and nullable provider usage. JobEvent is a per-job ordered durable activity stream. A job starts with a 120-second deadline. PostgreSQL skip-locked claims permit one owner per claim; each claim lasts 45 seconds and at most two attempts are allowed.

Execution locks the job, checks current ownership and fresh clocks, reserves 2,000 guard units, commits, then invokes the fixture provider without holding database locks. On completion it locks job then ticket, rechecks token/state/lease/deadline after the final lock, validates the response against fresh tenant-owned evidence, and atomically publishes the suggestion plus revision and activity. Cancellation locks the job and makes later publication ineligible. Recovery assigns a new random token; an old owner cannot publish errors, usage or success. Error reservations stay recorded. Missing usage is unknown; it is never inferred from guard reservations.

No network provider is implemented. The fixture boundary produces recorded success, ambiguous, transport, malformed, unsupported-promise and missing-usage cases. Strict validation requires approved categories, nonempty bounded reply, available source IDs, unique citations and null or nonnegative bounded integer usage. The same finite-language contract applies to provider and human replies: only compositions of up to 12 exact complete statements from PERMITTED_STATEMENTS are admitted, with whitespace normalization. The library contains no financial or resolution-time promise. This bounds permitted content deterministically; it makes no assertion about classifying unrestricted natural language. Reviewers retain category correction and statement selection, removal and ordering.

## HTTP boundary

Every protected request resolves membership. Ticket, job and evidence lookups include organization ownership and use 404 for foreign IDs. Review actor and tenant are server-owned. Django CSRF applies to every form mutation. A client cannot choose an organization through form fields. Import parsing is bounded by Django request size and domain caps. Templates escape customer text and drafts.

Views map forms and errors to domain services. Ordinary HTML forms are the baseline. HTMX polls only the activity panel every three seconds, ending when terminal or at the job deadline. It never refreshes an unsaved review form. Refresh observes persisted history and suggestions.
