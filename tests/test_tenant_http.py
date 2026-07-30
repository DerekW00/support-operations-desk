from django.test import Client
from support.models import Account, Source
from support.ingestion import ingest_ticket
from support.jobs import enqueue
from tests.test_ingestion import event


def test_session_required(client):
    assert client.get("/").status_code == 302


def test_foreign_pages_mutations_jobs_and_citations_are_hidden(domain):
    org, other, user, account, source = domain
    foreign_account = Account.objects.create(organization=other, name="Private", tier="standard")
    ticket, _ = ingest_ticket(other.pk, event(foreign_account))
    job = enqueue(other.pk, ticket.pk)
    c = Client()
    c.force_login(user)
    for method, url in [
        ("get", f"/tickets/{ticket.pk}/"),
        ("post", f"/tickets/{ticket.pk}/review/"),
        ("post", f"/jobs/{job.pk}/cancel/"),
    ]:
        assert getattr(c, method)(url).status_code == 404
    foreign_source = Source.objects.create(organization=other, title="private", body="secret")
    assert c.get(f"/sources/{foreign_source.pk}/").status_code == 404


def test_csrf_required_for_mutation(domain):
    _, _, user, _, _ = domain
    c = Client(enforce_csrf_checks=True)
    c.force_login(user)
    assert c.post("/import/", {"tickets": "[]"}).status_code == 403
