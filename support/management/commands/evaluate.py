from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from support.models import Account, Organization, Source, Ticket
from support.provider import InvalidSuggestion, suggest, validate_suggestion


class Command(BaseCommand):
    help = "Frozen functional fixture evaluation; not measured live-model quality."

    def handle(self, *args, **options):
        results = []
        with transaction.atomic():
            org = Organization.objects.create(name="Temporary fixture evaluation")
            account = Account.objects.create(organization=org, name="Synthetic", tier="standard")
            source = Source.objects.create(
                organization=org, title="Fixture source", body="Investigating."
            )
            for text, escalated, expected in [
                ("normal", False, "uncertain"),
                ("normal", True, "technical"),
                ("[transport-error]", False, "transport"),
                ("[malformed]", False, "invalid"),
                ("[promise]", False, "invalid"),
                ("[missing-usage]", False, "invalid"),
            ]:
                ticket = Ticket(
                    organization=org,
                    account=account,
                    customer_text=text,
                    escalated=escalated,
                    deadline=timezone.now(),
                )
                actual = ""
                try:
                    result = validate_suggestion(ticket, suggest(ticket, [source]), [source])
                    actual = result["category"]
                except ConnectionError:
                    actual = "transport"
                except InvalidSuggestion:
                    actual = "invalid"
                results.append(actual == expected)
            transaction.set_rollback(True)
        if not all(results):
            raise CommandError(f"Fixture evaluation failed: {results}")
        self.stdout.write(
            "Frozen functional evaluation: 6/6 passed. Live quality, latency and spend remain unmeasured."
        )
