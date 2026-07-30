from django.db import transaction
from django.http import Http404
from support.models import Membership, Review, Source, Ticket
from support.provider import InvalidSuggestion, validate_reply


class ReviewConflict(ValueError):
    pass


@transaction.atomic
def save_review(
    org_id: int,
    ticket_id: int,
    actor_id: int,
    expected_revision: int,
    category: str,
    reply: str,
    approved: bool,
) -> Review:
    try:
        ticket = Ticket.objects.select_for_update().get(pk=ticket_id, organization_id=org_id)
    except Ticket.DoesNotExist as exc:
        raise Http404 from exc
    if not Membership.objects.filter(organization_id=org_id, user_id=actor_id).exists():
        raise Http404
    if expected_revision != ticket.revision:
        raise ReviewConflict(
            "This review changed in another tab. Reload the latest revision before saving."
        )
    validate_reply(category, reply)
    suggestion = ticket.suggestions.first()
    source_ids = suggestion.source_ids if suggestion else []
    if Source.objects.filter(organization_id=org_id, pk__in=source_ids).count() != len(source_ids):
        raise InvalidSuggestion("Review references unavailable evidence.")
    ticket.revision += 1
    ticket.save(update_fields=["revision"])
    return Review.objects.create(
        ticket=ticket,
        actor_id=actor_id,
        revision=ticket.revision,
        category=category,
        reply=reply,
        approved=approved,
        source_ids=source_ids,
    )
