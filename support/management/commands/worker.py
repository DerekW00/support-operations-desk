import time
from django.core.management.base import BaseCommand
from support.jobs import claim, execute


class Command(BaseCommand):
    help = "Claim durable fixture jobs. --once handles at most one claim."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        while True:
            job = claim()
            if job:
                published = execute(job.pk, job.claim_token)
                self.stdout.write(
                    f"Job {job.pk}: " + ("published" if published else "no publication")
                )
            if options["once"]:
                return
            if not job:
                time.sleep(1)
