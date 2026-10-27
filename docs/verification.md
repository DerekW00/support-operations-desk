# Verification

Use the PostgreSQL environment from [README](../README.md). The development role needs permission to create the test database; there is no SQLite fallback.

## Commands

```sh
make verify
uv run playwright install chromium
BROWSER_EVIDENCE_DIR="$PWD/.browser-evidence" make browser
```

`make verify` checks frozen dependencies, Django configuration, migration drift, Ruff lint/format, mypy, all nonbrowser tests and the six frozen functional evaluations. Browser verification is a separate required workflow gate. `uv run pytest` runs the combined test suite.

Browser screenshots use a newly created temporary directory by default. Set `BROWSER_EVIDENCE_DIR` to retain them in a writable destination; the directory is created automatically. The repository ignores `.browser-evidence/`.

## Recorded result

On 2026-10-26 at code commit `8b77bb8498cc68a535746d691e7aa843094b06cd`, verification passed with Python 3.12.15 and PostgreSQL 16.15: **43 nonbrowser tests, one Chromium workflow, and 6/6 frozen fixture evaluations**. Static checks and migration drift checks passed. Full execution logs were retained outside this repository during development; this public checkout includes the [synthetic workflow screenshot](images/workflow-review.jpg).

## Behavioral coverage

- Policy boundaries and customer prompt-injection nonauthority.
- Exact/conflicting import retries, batch rollback/caps and concurrent changed events.
- Stale review revisions, bounded statement composition, independent provider/human commitment rejection, and A → approve → B → reload provenance.
- Missing/old/forged evidence bases, invalid citations, explicit provider errors and unknown usage.
- Concurrent claims, cancellation/reclaim/expiry fences and publication expiry while waiting for the final ticket lock.
- Tenant HTTP boundaries, session/CSRF requirements, portable artifact destinations and application-specific cookie names.
- Chromium login, urgent queue, job execution, citations, editing/approval/reload, stale second tab and a newer differently cited suggestion requiring review.

Concurrency tests open separate PostgreSQL connections. The final-lock expiry regression uses actual row locks and elapsed time. Browser verification runs the worker on another database thread.

Development retained behavioral RED and GREEN evidence, including the original promise/provenance defects and their fixes. Missing imports, selector mistakes and harness errors were recorded separately rather than counted as behavioral failures.

These checks exercise synthetic local behavior. No live API calls, model benchmarks, deployments or production measurements were performed.
