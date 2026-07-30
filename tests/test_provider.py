import pytest
from support.ingestion import ingest_ticket
from support.jobs import enqueue, claim, execute
from support.models import SuggestionRecord
from tests.test_ingestion import event


@pytest.mark.parametrize("marker", ["[malformed]", "[promise]", "[missing-usage]"])
def test_recorded_invalid_results_never_publish(domain, marker):
    org, _, _, account, _ = domain
    ticket, _ = ingest_ticket(org.pk, event(account, text=marker))
    job = enqueue(org.pk, ticket.pk)
    lease = claim()
    assert not execute(job.pk, lease.claim_token)
    job.refresh_from_db()
    assert job.state == "failed" and job.provider_usage is None
    assert job.guard_reserved == 2000 and not SuggestionRecord.objects.exists()


def test_retries_stop_at_two_calls(domain):
    org, _, _, account, _ = domain
    ticket, _ = ingest_ticket(org.pk, event(account, text="[transport-error]"))
    job = enqueue(org.pk, ticket.pk)
    for _ in range(2):
        lease = claim()
        assert lease is not None
        assert not execute(job.pk, lease.claim_token)
    assert claim() is None
    job.refresh_from_db()
    assert job.state == "failed" and job.attempts == 2 and job.guard_reserved == 4000
