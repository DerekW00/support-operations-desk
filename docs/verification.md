# Verification

Run setup/migration from README before make verify. PostgreSQL is required for domain tests and creates test_support_ops; the configured local development user needs CREATEDB. There is no SQLite fallback.

## Required gates

- uv sync --frozen: committed lockfile and CPython >=3.12,<3.13.
- python manage.py check and makemigrations --check --dry-run.
- Ruff lint and format checks.
- mypy over support, config and manage.py using Django stubs.
- pytest against real PostgreSQL: policy boundaries, prompt-injection nonauthority, exact/conflicting retries, bulk rollback/caps, concurrent changed events, revision conflicts, invalid promises/citations, provider errors/usage, claim races, cancellation/reclaim/expiry fences, actual publication lock-wait expiry, tenant HTTP boundaries and CSRF.
- python manage.py evaluate: six frozen functional expectations, rolled back after execution.
- pytest tests/test_browser.py: Chromium login, urgent queue, fixture job, citations, edit/approval/reload and stale second tab, with screenshots.

The browser test runs the worker through a separate database thread while the browser session stays open. The lock-wait regression uses actual PostgreSQL locks and elapsed wall time, not a mocked clock. Concurrency tests open separate database connections.

## Evidence

Evidence is outside Git at /Users/dw/code/portfolio-python/python-evidence/support-operations-desk/. Genuine missing-behavior failures are retained in red-behavior.log; focused regression logs cover import/commands, changed-event race, polling expiry, new suggestion revision and final-lock deadline expiry. GREEN logs, final verification output, browser output and implementation-report.md record observed outcomes. approved-review.png, stale-conflict.png and workflow-review.jpg show the tested review workflow.

The RED logs also preserve initial test-harness issues where present. Missing imports/configuration and selector mistakes are not represented as behavioral proof. red-behavior.log is the explicit PostgreSQL 20-failure behavioral baseline; red-lock-wait.log is the real lock-expiry reproducer. make verify excludes the browser only because it is run separately as an explicit required gate.

No live API calls, live-model benchmarks, deployments or production measurements are part of these checks.
