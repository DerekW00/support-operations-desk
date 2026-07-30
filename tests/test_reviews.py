import pytest
from support.ingestion import ingest_ticket
from support.reviews import save_review, ReviewConflict
from support.provider import InvalidSuggestion, validate_suggestion
from support.models import Review, Source
from tests.test_ingestion import event


def test_stale_approval_cannot_overwrite_history(domain):
    org, _, user, account, _ = domain
    ticket, _ = ingest_ticket(org.pk, event(account))
    first = save_review(org.pk, ticket.pk, user.pk, 0, "technical", "We are investigating.", True)
    with pytest.raises(ReviewConflict):
        save_review(org.pk, ticket.pk, user.pk, 0, "billing", "replacement", True)
    assert Review.objects.get(pk=first.pk).reply == "We are investigating."
    assert Review.objects.count() == 1


@pytest.mark.parametrize(
    "reply",
    ["We guarantee resolution tomorrow.", "We will issue a refund.", "A credit is guaranteed."],
)
def test_unsupported_promises_rejected(domain, reply):
    org, _, user, account, _ = domain
    ticket, _ = ingest_ticket(org.pk, event(account))
    with pytest.raises(InvalidSuggestion):
        save_review(org.pk, ticket.pk, user.pk, 0, "technical", reply, True)


def test_foreign_and_unknown_citations_rejected(domain):
    org, other, _, account, source = domain
    ticket, _ = ingest_ticket(org.pk, event(account))
    foreign = Source.objects.create(organization=other, title="Other", body="private")
    for ids in ([foreign.pk], [999999]):
        with pytest.raises(InvalidSuggestion):
            validate_suggestion(
                ticket,
                {
                    "category": "technical",
                    "reply": "Investigating.",
                    "source_ids": ids,
                    "usage": None,
                },
                [source],
            )


def test_new_suggestion_invalidates_an_open_review(domain):
    from support.jobs import claim, enqueue, execute

    org, _, user, account, _ = domain
    ticket, _ = ingest_ticket(org.pk, event(account))
    old_revision = ticket.revision
    job = enqueue(org.pk, ticket.pk)
    lease = claim()
    assert execute(job.pk, lease.claim_token)
    with pytest.raises(ReviewConflict):
        save_review(
            org.pk, ticket.pk, user.pk, old_revision, "technical", "An old tab reply.", True
        )
