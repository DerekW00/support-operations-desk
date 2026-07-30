import hashlib
import json
from dataclasses import asdict, dataclass
from django.db import transaction
from django.utils import timezone
from support.models import Account, Organization, Outage, Ticket
from support.policy import compute_sla


class InvalidImport(ValueError):
    pass


class ImportConflict(ValueError):
    pass


@dataclass(frozen=True)
class TicketInput:
    event_id: str
    account_id: int
    subject: str
    text: str


def _validate(event: TicketInput) -> None:
    for value, cap in [(event.event_id, 100), (event.subject, 160), (event.text, 8000)]:
        if not isinstance(value, str) or not value.strip() or len(value) > cap:
            raise InvalidImport(
                "Event ID, subject and customer text must be nonempty and within caps."
            )
    if type(event.account_id) is not int:
        raise InvalidImport("Account ID must be an integer.")


@transaction.atomic
def ingest_ticket(org_id: int, event: TicketInput) -> tuple[Ticket, bool]:
    _validate(event)
    Organization.objects.select_for_update().get(pk=org_id)
    # Organization then account is the consistent import lock order.
    try:
        account = Account.objects.select_for_update().get(
            pk=event.account_id, organization_id=org_id
        )
    except Account.DoesNotExist as exc:
        raise InvalidImport("Unknown account.") from exc
    digest = hashlib.sha256(
        json.dumps(asdict(event), sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    existing = Ticket.objects.filter(organization_id=org_id, event_id=event.event_id).first()
    if existing:
        if existing.payload_hash != digest:
            raise ImportConflict("Source event already exists with different content.")
        return existing, False
    now = timezone.now()
    verified = Outage.objects.filter(
        organization_id=org_id, account=account, active=True, verified=True
    ).exists()
    policy = compute_sla(account.tier, verified, now)
    ticket = Ticket.objects.create(
        organization_id=org_id,
        account=account,
        event_id=event.event_id,
        payload_hash=digest,
        subject=event.subject,
        customer_text=event.text,
        received_at=now,
        deadline=policy.deadline,
        escalated=policy.escalated,
    )
    return ticket, True


@transaction.atomic
def ingest_bulk(org_id: int, events: list[TicketInput], raw_size: int = 0) -> list[Ticket]:
    if len(events) > 50 or raw_size > 262144:
        raise InvalidImport("Imports allow at most 50 tickets and 256 KiB.")
    # Stable account lock ordering avoids cross-account bulk deadlocks.
    return [ingest_ticket(org_id, event)[0] for event in sorted(events, key=lambda e: e.account_id)]
