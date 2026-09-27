# Support Operations Desk

A Python/Django support review workspace: import synthetic customer tickets, prioritize by deterministic SLA policy, inspect cited fixture drafts, and record an immutable human decision. No reply is sent externally.

## Run locally

Requirements: CPython 3.12, uv, PostgreSQL 16, and a database user permitted to create a test database. No AI credentials are used.

```sh
uv sync --frozen
export DEMO_MODE=1
export PGHOST=127.0.0.1 PGPORT=15531 PGDATABASE=support_ops PGUSER=support
# Start your own PostgreSQL 16 and create support_ops, or use the optional
# local-only compose.yaml: docker compose up -d database
uv run python manage.py migrate
uv run python manage.py demo
uv run python manage.py runserver 127.0.0.1:8101
```

Open http://127.0.0.1:8101/ and sign in as **demo** with **local-demo-review-2026**. The second synthetic tenant is **other-demo**, using the same local demonstration password. Accounts are created only with explicit DEMO_MODE=1. These are synthetic application accounts, never infrastructure credentials.

For this verified VPS checkout, use the existing private PostgreSQL instance instead of Compose:

```sh
. /Users/dw/code/portfolio-python/execution/runtime-env.sh
export PGHOST=/Users/dw/code/portfolio-python/.runtime/pg16/support/socket
export PGPORT=15531 PGDATABASE=support_ops PGUSER=dw
uv run python manage.py migrate
uv run python manage.py demo
uv run python manage.py runserver 127.0.0.1:8101
```

`demo` persists the outage and ambiguous drafts plus rejected-promise and failed-provider examples. It is repeatable without overwriting existing decisions. `seed_demo` only creates fixtures. To generate a new suggestion, press **Generate fixture suggestion**, then run a worker in another shell with the same environment:

```sh
uv run python manage.py worker --once
# Or continuously: uv run python manage.py worker
```

The worker handles one claim per --once invocation. A recorded transport failure is retried up to two attempts. Refresh to load the saved suggestion; status polling does not replace an unsaved form.

## Workflow

1. Open the urgent workspace ticket: its verified account outage gives a one-hour SLA.
2. Inspect the cited synthetic availability guidance.
3. Correct the category and compose a reply from the displayed approved statement library, then approve. Approval creates an append-only revision; nothing is emailed.
The reply contract is deliberately bounded: add, remove, or reorder up to 12 exact library statements, separated by whitespace. Custom prose is rejected at both provider and human-review boundaries. This is a deterministic permitted-language contract, not an unrestricted natural-language safety claim. A newly generated suggestion loads its own content and evidence as unapproved; historical approvals stay attached to their original basis.

4. Open the same ticket in two tabs. Save one, then submit the other: the stale revision visibly conflicts.
5. Inspect the refund-request ticket: the frozen provider's financial/timing promise is rejected. Customer text cannot grant entitlements.
6. Import JSON through **Import tickets**. Account IDs are listed on that page; only the signed-in organization is available.

Imports accept an array of `event_id`, `account_id`, `subject`, and `text` objects. A repeat event with identical canonical content returns its prior ticket; changed content conflicts. One invalid member rolls back the entire import. Limits are 50 tickets, 256 KiB request body, 8,000 customer characters, 160 subject characters, and 100 event-ID characters.

## Verify

After migration, with PostgreSQL configured:

```sh
make verify
# Browser installation needed on a new workstation only:
uv run playwright install chromium
make browser
# Complete combined suite:
uv run pytest
```

The verified VPS already has project-local Chromium and its required shared libraries; source runtime-env.sh and do not reinstall system dependencies. Browser evidence defaults to a newly created writable temporary directory. Set `BROWSER_EVIDENCE_DIR="$PWD/.browser-evidence" make browser` to retain screenshots in an ignored checkout-local directory, or supply any writable destination. Verified VPS gates explicitly set the canonical external evidence directory.

`make verify` checks the frozen dependency graph, Django configuration, migration drift, Ruff lint/format, mypy, all nonbrowser PostgreSQL tests and the six-case fixture evaluation. Browser journeys are a separate required delivery gate. See [verification](docs/verification.md), [architecture](docs/architecture.md), [tradeoffs](docs/tradeoffs.md), [contributions](docs/contributions.md), and [provenance](docs/data-provenance.md).

## Scope

This is an authenticated local portfolio product using frozen scripted responses. Live-model quality, latency, spend, production scale and business impact are unmeasured. Production hosting, email delivery, SSO, organization switching, arbitrary attachments and live providers are outside this implementation. Outside demo mode set DJANGO_SECRET_KEY explicitly and supply deployment-specific secure-cookie/TLS/host configuration before considering hosting.

Same-host demo cookies use `support_ops_session` and `support_ops_csrf`, so the three loopback products can retain separate sessions and CSRF forms across ports. Cookie domain/path and CSRF enforcement retain their normal Django scope.
