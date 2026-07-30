from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from datetime import timedelta
import pytest
from django.db import close_old_connections
from django.test import Client
from django.utils import timezone
from support.models import Account, Job, Ticket
from support.ingestion import ingest_ticket, ImportConflict
from support.jobs import enqueue
from tests.test_ingestion import event


@pytest.mark.django_db(transaction=True)
def test_concurrent_changed_event_has_one_import_and_one_conflict(domain):
    org, _, _, account, _ = domain
    second = Account.objects.create(organization=org, name="Second account", tier="standard")
    barrier = Barrier(2)

    def ingest(a):
        close_old_connections()
        barrier.wait()
        try:
            ingest_ticket(org.pk, event(a))
            return "created"
        except ImportConflict:
            return "conflict"
        finally:
            close_old_connections()

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(ingest, [account, second]))
    assert sorted(results) == ["conflict", "created"]
    assert Ticket.objects.count() == 1


def test_polling_stops_after_deadline(domain):
    org, _, user, account, _ = domain
    ticket, _ = ingest_ticket(org.pk, event(account))
    job = enqueue(org.pk, ticket.pk)
    Job.objects.filter(pk=job.pk).update(deadline=timezone.now() - timedelta(seconds=1))
    c = Client()
    c.force_login(user)
    response = c.get(f"/jobs/{job.pk}/status/")
    assert response.status_code == 200
    assert b'hx-trigger="every' not in response.content
