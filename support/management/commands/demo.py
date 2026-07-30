from django.core.management import call_command
from django.core.management.base import BaseCommand
from support.jobs import claim, enqueue, execute
from support.models import Organization, Ticket


class Command(BaseCommand):
    help = "Seed and run deterministic synthetic support examples."

    def handle(self, *args, **options):
        call_command("seed_demo", stdout=self.stdout)
        org = Organization.objects.get(name="Northstar Software")
        for ticket in Ticket.objects.filter(organization=org):
            if not ticket.jobs.exists():
                enqueue(org.pk, ticket.pk)
        for _ in range(12):
            job = claim()
            if job is None:
                break
            execute(job.pk, job.claim_token)
        self.stdout.write(
            "Demo persisted: outage escalation, ambiguous complaint, rejected promise, recorded transport failure. Open http://127.0.0.1:8101/"
        )
