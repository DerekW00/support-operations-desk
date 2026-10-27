# Support Operations Desk

A support lead's workspace for turning an incoming ticket into a reviewed decision. Import synthetic tickets, prioritize by account policy, inspect a cited draft, correct its category and language, and approve a specific revision. Approval records a decision; it never sends a customer message.

Built with **Python 3.12, Django 5.2, PostgreSQL 16, server-rendered HTML/CSS and local HTMX**. The provider uses frozen fixtures: no API key or external AI service is needed.

![Synthetic support ticket with cited guidance, review form and decision history](docs/images/workflow-review.jpg)

*Chromium screenshot of the synthetic review workflow. All names, messages and source material are generated demonstration data.*

## What this project demonstrates

The engineering problem is keeping a draft's authority, evidence and approval separate while work happens concurrently:

- Deterministic account/outage records own SLA and escalation. Customer instructions cannot grant policy authority.
- Canonical event hashes make exact imports idempotent; conflicting reuse fails without mutation, and invalid batches roll back.
- Django sessions, CSRF and server-owned organization membership scope tickets, jobs and citations. A second synthetic tenant exercises isolation.
- PostgreSQL jobs use leases, random claim tokens and a fresh ownership/deadline check after publication locks. Cancelled, expired or reclaimed workers cannot publish late.
- Human decisions bind a ticket revision to an explicit suggestion and source snapshot. A newer suggestion requires fresh review; stale tabs conflict.
- Provider usage remains unknown when unavailable. Admission reservations are never presented as billing.

## Run locally

Prerequisites: Python 3.12, [uv](https://docs.astral.sh/uv/), a running PostgreSQL 16 instance, and a local development PostgreSQL role with database creation permission. Run these commands from the cloned repository root. The example assumes that your local PostgreSQL role matches your shell username; substitute your role and connection settings where needed.

```sh
uv sync --frozen --python 3.12
export DEMO_MODE=1
export PGHOST=127.0.0.1 PGPORT=5432
export PGUSER="$USER" PGDATABASE=support_ops
# If your local PostgreSQL requires a password, supply it using your normal local configuration.
createdb --host="$PGHOST" --port="$PGPORT" --username="$PGUSER" "$PGDATABASE"
uv run python manage.py migrate
uv run python manage.py seed_demo
uv run python manage.py runserver 127.0.0.1:8101
```

Skip `createdb` if that database already exists. Keep this database separate from other projects. Django reads exported environment variables; it does not automatically load `.env`. Explicitly set all four `PG*` variables above so the checkout's original local verification defaults are not used.

Open **http://127.0.0.1:8101/** and sign in with **demo / local-demo-review-2026**. The second tenant is **other-demo**, with the same password. These are intentionally public, synthetic application credentials created only when `DEMO_MODE=1`; use them only for this local demonstration.

In another terminal, export the same environment and start the fixture worker:

```sh
export DEMO_MODE=1
export PGHOST=127.0.0.1 PGPORT=5432 PGUSER="$USER" PGDATABASE=support_ops
uv run python manage.py worker
# Alternatively, claim at most one queued job:
# uv run python manage.py worker --once
```

For a ready-made scenario, `uv run python manage.py demo` seeds the same data and runs the outage, ambiguity, rejected-promise and transport-failure fixtures. It preserves existing decisions. Run it before starting a continuous worker if you want deterministic command-line demonstration output.

### Try the workflow

1. Open **Urgent: workspace unavailable**. Its verified outage gives it a one-hour SLA.
2. Click **Generate fixture suggestion**. The worker persists a draft; reload to inspect its cited guidance.
3. Correct the category and compose a reply using the displayed approved statements. Approve, then reload to see the saved decision and history.
4. Open the ticket in two tabs. Save one, then submit the other to see the stale-revision conflict.
5. Generate a newer suggestion. It loads as needing review while earlier approval remains historical.
6. Import a JSON batch using an account ID listed on the import page. Exact retries return the existing ticket; changed content under the same event ID conflicts.

Replies deliberately use a **finite statement library**, with up to 12 exact statements that can be added, removed or reordered, separated by whitespace. Custom prose is rejected at provider and human-review boundaries. This trades expressive freedom for a demonstrable permitted-language contract; it is not a general natural-language safety classifier.

Imports allow 50 tickets, a 256 KiB request body, 8,000 message characters, 160 subject characters and 100 event-ID characters.

### Optional Compose database

`compose.yaml` supplies a separate PostgreSQL 16 database on loopback port **15531**:

```sh
docker compose up -d database
export DEMO_MODE=1
export PGHOST=127.0.0.1 PGPORT=15531 PGUSER=support PGDATABASE=support_ops
# The container creates the database; continue with migrate, seed_demo and runserver above.
```

This optional local route uses trust authentication and was **not executed in the recorded verification**. Keep it local. Verification used PostgreSQL 16 directly.

## Verify

With the same PostgreSQL environment exported, the database role also needs permission to create `test_support_ops`.

```sh
make verify
uv run playwright install chromium
BROWSER_EVIDENCE_DIR="$PWD/.browser-evidence" make browser
# Or run all pytest cases together:
uv run pytest
```

Chromium may require platform dependencies on a new workstation. `BROWSER_EVIDENCE_DIR` selects a writable screenshot destination; the directory is created automatically. Without it, browser tests use a new temporary directory. `.browser-evidence/` is ignored by Git.

Recorded at tested code commit **`8b77bb8498cc68a535746d691e7aa843094b06cd`**:

| Check | Observed result |
| --- | --- |
| Frozen dependencies, Django checks and migration drift | Passed |
| Ruff lint/format and mypy | Passed |
| Nonbrowser tests on PostgreSQL 16.15 / Python 3.12.15 | 43 passed |
| Chromium workflow | 1 passed |
| Frozen fixture evaluation | 6/6 passed |

These are functional checks of synthetic scenarios. They do not measure live-model quality, production scale, customer impact, latency or spend. The documentation/license commit follows the tested code commit without changing runtime behavior.

## Design and scope

Read the [architecture](docs/architecture.md), [tradeoffs](docs/tradeoffs.md), [verification approach](docs/verification.md), [data provenance](docs/data-provenance.md), and [contribution/AI assistance notes](docs/contributions.md).

This is a local portfolio application. Live providers, outbound messaging, SSO, organization switching and production hosting are outside scope. Demo mode uses local demonstration settings; production hosting would require a separate deployment design.

The implementation was created with Codex assistance covering code, synthetic fixtures, tests, documentation and verification. No employer source, private records or private assets were imported.

## License

Original project material is available under the [MIT License](LICENSE), copyright 2026 Derek Derui Wang. Third-party packages retain their own licenses; vendored HTMX includes its [Zero-Clause BSD license](static/vendor/HTMX-LICENSE.txt).
