import pytest
from django.test import Client
from support.ingestion import ingest_ticket
from support.jobs import enqueue, claim, execute
from support.models import Source, Review
from support.provider import InvalidSuggestion, validate_suggestion
from support.reviews import save_review
from tests.test_ingestion import event


@pytest.mark.parametrize("boundary", ["provider", "review"])
@pytest.mark.parametrize("reply", ["We will return your payment.", "We will resolve this by 5pm."])
def test_unapproved_commitments_rejected_at_provider_and_review(domain, reply, boundary):
    org, _, user, account, source = domain
    ticket, _ = ingest_ticket(org.pk, event(account))
    with pytest.raises(InvalidSuggestion):
        if boundary == "provider":
            validate_suggestion(
                ticket,
                {"category": "billing", "reply": reply, "source_ids": [source.pk], "usage": None},
                [source],
            )
        else:
            save_review(org.pk, ticket.pk, user.pk, 0, "billing", reply, True)
    assert not Review.objects.exists()


def test_only_bounded_statements_can_be_composed(domain):
    org, _, user, account, _ = domain
    ticket, _ = ingest_ticket(org.pk, event(account))
    with pytest.raises(InvalidSuggestion):
        save_review(org.pk, ticket.pk, user.pk, 0, "technical", "A freely invented sentence.", True)
    review = save_review(
        org.pk,
        ticket.pk,
        user.pk,
        0,
        "technical",
        "Thank you for reporting this. We are investigating.",
        False,
    )
    assert review.reply == "Thank you for reporting this. We are investigating."


def publish(ticket, org, source, reply):
    job = enqueue(org.pk, ticket.pk)
    lease = claim()
    assert lease.pk == job.pk
    assert execute(
        job.pk,
        lease.claim_token,
        lambda t, s: {
            "category": "technical",
            "reply": reply,
            "source_ids": [source.pk],
            "usage": None,
        },
    )
    ticket.refresh_from_db()
    return ticket.suggestions.first()


def test_new_suggestion_reload_requires_fresh_content_and_evidence_review(domain):
    org, _, user, account, source_a = domain
    source_b = Source.objects.create(
        organization=org, title="Account guidance B", body="Synthetic B"
    )
    ticket, _ = ingest_ticket(org.pk, event(account))
    a = publish(ticket, org, source_a, "We are investigating.")
    client = Client()
    client.force_login(user)
    page = client.get(f"/tickets/{ticket.pk}/")
    form = page.context["form"].initial
    response = client.post(
        f"/tickets/{ticket.pk}/review/",
        {**form, "category": "technical", "reply": "We are investigating.", "action": "approve"},
    )
    assert response.status_code == 302
    original = ticket.reviews.first()
    assert original.source_ids == [source_a.pk]
    b = publish(ticket, org, source_b, "We are reviewing the account details.")
    page = client.get(f"/tickets/{ticket.pk}/")
    form = page.context["form"].initial
    assert form["reply"] == "We are reviewing the account details."
    assert form["basis_suggestion_id"] == b.pk
    assert page.context["current_approved"] is False
    assert b"New suggestion requires review" in page.content
    response = client.post(f"/tickets/{ticket.pk}/review/", {**form, "action": "approve"})
    assert response.status_code == 302
    latest = ticket.reviews.first()
    original.refresh_from_db()
    assert original.reply == "We are investigating." and original.source_ids == [source_a.pk]
    assert latest.reply == "We are reviewing the account details." and latest.source_ids == [
        source_b.pk
    ]
    assert latest.basis_suggestion_id == b.pk
    assert page.context["suggestion"].pk != a.pk


@pytest.mark.parametrize("basis", ["old", "missing", "foreign"])
def test_http_cannot_rebind_approval_to_unreviewed_basis(domain, basis):
    org, other, user, account, source_a = domain
    source_b = Source.objects.create(organization=org, title="B", body="B")
    ticket, _ = ingest_ticket(org.pk, event(account))
    a = publish(ticket, org, source_a, "We are investigating.")
    b = publish(ticket, org, source_b, "We are reviewing the account details.")
    client = Client()
    client.force_login(user)
    form = client.get(f"/tickets/{ticket.pk}/").context["form"].initial
    form["basis_suggestion_id"] = {"old": a.pk, "missing": "", "foreign": 999999}[basis]
    response = client.post(f"/tickets/{ticket.pk}/review/", {**form, "action": "approve"})
    assert response.status_code == 409
    assert not Review.objects.filter(ticket=ticket).exists()
    assert b.source_ids == [source_b.pk]
