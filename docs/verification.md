# Verification

Run setup/migration from README before make verify. PostgreSQL is required for domain tests and creates test_support_ops; the configured local development user needs CREATEDB. There is no SQLite fallback.

## Required gates

- uv sync --frozen: committed lockfile and CPython >=3.12,<3.13.
- python manage.py check and makemigrations --check --dry-run.
- Ruff lint and format checks.
- mypy over support, config and manage.py using Django stubs.
- pytest against real PostgreSQL: policy boundaries, prompt-injection nonauthority, exact/conflicting retries, bulk rollback/caps, concurrent changed events, revision conflicts, bounded statement compositions, independent provider/human commitment rejection, A→approve→B→reload provenance, missing/old/forged evidence bases, invalid citations, provider errors/usage, claim races, cancellation/reclaim/expiry fences, actual publication lock-wait expiry, tenant HTTP boundaries and CSRF.
- python manage.py evaluate: six frozen functional expectations, rolled back after execution.
- pytest tests/test_browser.py: Chromium login, urgent queue, fixture job, citations, edit/approval/reload and stale second tab, followed by a new differently cited suggestion, unapproved refresh state, blocked custom payment commitment and fresh approval, with screenshots.

The browser test runs the worker through a separate database thread while the browser session stays open. The lock-wait regression uses actual PostgreSQL locks and elapsed wall time, not a mocked clock. Concurrency tests open separate database connections.

## Evidence

Evidence is outside Git at /Users/dw/code/portfolio-python/python-evidence/support-operations-desk/. Genuine missing-behavior failures are retained in red-behavior.log; focused regression logs cover import/commands, changed-event race, polling expiry, new suggestion revision and final-lock deadline expiry. GREEN logs, final verification output, browser output and implementation-report.md record observed outcomes. approved-review.png, stale-conflict.png and workflow-review.jpg show the tested review workflow.

The RED logs also preserve initial test-harness issues where present. Missing imports/configuration and selector mistakes are not represented as behavioral proof. red-behavior.log is the explicit PostgreSQL 20-failure behavioral baseline; red-lock-wait.log is the real lock-expiry reproducer. make verify excludes the browser only because it is run separately as an explicit required gate.

No live API calls, live-model benchmarks, deployments or production measurements are part of these checks.

Fix-round evidence is retained in fix1-red-review-findings.log (four original behavioral failures), fix1-red-independent-boundaries.log (seven independent failures against the reviewed boundary code with fixes restored in finally), fix1-green-review-findings.log, fix1-verify-final.log and fix1-pytest-final.log. new-evidence-review.png shows the superseding suggestion awaiting review.

Whole-delivery portability: browser artifacts use a writable temporary directory by default; BROWSER_EVIDENCE_DIR overrides/creates the destination (for example `$PWD/.browser-evidence`). Final VPS evidence explicitly sets BROWSER_EVIDENCE_DIR=/Users/dw/code/portfolio-python/python-evidence/support-operations-desk. Per-product session/CSRF cookie names preserve same-browser logins across loopback ports; a retained cross-product Playwright probe exercises concurrent sessions and saved CSRF forms without disabling protection.
