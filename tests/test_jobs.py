from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import pytest
from django.db import close_old_connections
from django.utils import timezone
from support.ingestion import ingest_ticket
from support.jobs import enqueue, claim, execute, cancel
from support.models import Job, SuggestionRecord
from tests.test_ingestion import event


def test_transport_error_reserves_guard_but_usage_unknown(domain):
    org, _, _, account, _ = domain
    ticket, _ = ingest_ticket(org.pk, event(account, text="[transport-error]"))
    job = enqueue(org.pk, ticket.pk)
    lease = claim()
    assert execute(lease.pk, lease.claim_token) is False
    job.refresh_from_db()
    assert job.guard_reserved == 2000 and job.provider_usage is None
    assert job.state == "queued"


@pytest.mark.parametrize("terminal", ["cancel", "expired", "reclaimed"])
def test_late_provider_cannot_publish(domain, terminal):
    org, _, _, account, source = domain
    ticket, _ = ingest_ticket(org.pk, event(account))
    job = enqueue(org.pk, ticket.pk)
    lease = claim()
    token = lease.claim_token

    def delayed(ticket, sources):
        if terminal == "cancel":
            cancel(org.pk, job.pk)
        elif terminal == "expired":
            Job.objects.filter(pk=job.pk).update(deadline=timezone.now() - timedelta(seconds=1))
        else:
            Job.objects.filter(pk=job.pk).update(lease_until=timezone.now() - timedelta(seconds=1))
            claim()
        return {
            "category": "technical",
            "reply": "We are investigating.",
            "source_ids": [source.pk],
            "usage": None,
        }

    assert execute(job.pk, token, provider=delayed) is False
    assert not SuggestionRecord.objects.filter(ticket=ticket).exists()


@pytest.mark.django_db(transaction=True)
def test_concurrent_claims_have_one_owner(domain):
    org, _, _, account, _ = domain
    ticket, _ = ingest_ticket(org.pk, event(account))
    enqueue(org.pk, ticket.pk)

    def take():
        close_old_connections()
        result = claim()
        close_old_connections()
        return result.pk if result else None

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: take(), range(2)))
    assert sum(item is not None for item in results) == 1


@pytest.mark.django_db(transaction=True)
def test_publication_rechecks_deadline_after_waiting_for_ticket_lock(domain):
    import time
    from threading import Event
    from django.db import transaction
    from support.models import Ticket

    org, _, _, account, source = domain
    ticket, _ = ingest_ticket(org.pk, event(account))
    job = enqueue(org.pk, ticket.pk)
    lease = claim()
    Job.objects.filter(pk=job.pk).update(deadline=timezone.now() + timedelta(seconds=1))
    provider_returned = Event()

    def provider(ticket, sources):
        provider_returned.set()
        return {
            "category": "technical",
            "reply": "We are investigating.",
            "source_ids": [source.pk],
            "usage": None,
        }

    def run():
        close_old_connections()
        result = execute(job.pk, lease.claim_token, provider=provider)
        close_old_connections()
        return result

    with ThreadPoolExecutor(max_workers=1) as pool:
        with transaction.atomic():
            Ticket.objects.select_for_update().get(pk=ticket.pk)
            pending = pool.submit(run)
            assert provider_returned.wait(5)
            time.sleep(1.2)
        assert pending.result(timeout=5) is False
    assert not SuggestionRecord.objects.filter(ticket=ticket).exists()
