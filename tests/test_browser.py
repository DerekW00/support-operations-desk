from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from django.db import close_old_connections
import pytest
from playwright.sync_api import sync_playwright
from support.ingestion import ingest_ticket
from support.jobs import claim, execute
from support.models import Outage, Source
from tests.test_ingestion import event


@pytest.mark.django_db(transaction=True)
def test_outage_review_and_stale_tab(live_server, domain):
    org, _, _, account, _ = domain
    Outage.objects.create(
        organization=org, account=account, verified=True, title="Verified synthetic outage"
    )
    ticket, _ = ingest_ticket(org.pk, event(account, subject="Urgent: workspace unavailable"))
    source_b = Source.objects.create(
        organization=org, title="New account guidance", body="Synthetic B"
    )
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1200, "height": 900})
        page = context.new_page()
        page.goto(live_server.url + "/")
        page.get_by_label("Username").fill("reviewer")
        page.get_by_label("Password").fill("test-password")
        page.get_by_role("button", name="Sign in").click()
        page.get_by_role("link", name="Urgent: workspace unavailable", exact=True).click()
        assert page.get_by_text("Verified outage · 1h SLA").count() == 1
        page.get_by_role("button", name="Generate fixture suggestion").click()

        def work():
            close_old_connections()
            lease = claim()
            result = lease is not None and execute(lease.pk, lease.claim_token)
            close_old_connections()
            return result

        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(work).result()
        page.reload()
        assert page.get_by_role("link", name="Availability").count() >= 1
        other = context.new_page()
        other.goto(page.url)
        page.get_by_label("Draft reply").fill("We are investigating the service interruption.")
        page.get_by_role("button", name="Approve revision").click()
        assert page.get_by_text("Approved", exact=True).count() >= 1
        page.reload()
        assert (
            page.get_by_label("Draft reply").input_value()
            == "We are investigating the service interruption."
        )
        other.get_by_label("Draft reply").fill("An obsolete reply.")
        other.get_by_role("button", name="Approve revision").click()
        assert other.get_by_role("alert").inner_text().startswith("This review changed")
        evidence = Path("/Users/dw/code/portfolio-python/python-evidence/support-operations-desk")
        page.screenshot(path=str(evidence / "approved-review.png"), full_page=True)
        page.screenshot(path=str(evidence / "workflow-review.jpg"), type="jpeg", quality=70)
        other.screenshot(path=str(evidence / "stale-conflict.png"), full_page=True)
        page.get_by_role("button", name="Generate fixture suggestion").click()

        def new_suggestion():
            close_old_connections()
            lease = claim()
            result = execute(
                lease.pk,
                lease.claim_token,
                lambda t, s: {
                    "category": "account",
                    "reply": "We are reviewing the account details.",
                    "source_ids": [source_b.pk],
                    "usage": None,
                },
            )
            close_old_connections()
            return result

        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(new_suggestion).result()
        page.reload()
        assert (
            page.get_by_label("Draft reply").input_value()
            == "We are reviewing the account details."
        )
        assert page.locator(".review-panel").get_by_text("Needs review", exact=True).count() == 1
        assert page.get_by_text("New suggestion requires review.", exact=False).count() == 1
        assert page.get_by_role("link", name="New account guidance", exact=True).count() == 1
        page.screenshot(path=str(evidence / "new-evidence-review.png"), full_page=True)
        page.get_by_label("Draft reply").fill("We will return your payment.")
        page.get_by_role("button", name="Approve revision").click()
        assert page.get_by_role("alert").inner_text().startswith("Use only the approved statements")
        page.get_by_label("Draft reply").fill("We are reviewing the account details.")
        page.get_by_role("button", name="Approve revision").click()
        assert page.locator(".review-panel").get_by_text("Approved", exact=True).count() == 1
        browser.close()
