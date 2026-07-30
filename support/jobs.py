from collections.abc import Callable
from datetime import timedelta
from uuid import UUID, uuid4
from django.db import transaction
from django.db.models import Max, Q
from django.http import Http404
from django.utils import timezone
from support.models import Job, JobEvent, Source, SuggestionRecord, Ticket
from support.provider import suggest, validate_suggestion

Provider = Callable[[Ticket, list[Source]], object]


def _event(job: Job, kind: str, detail: str = "") -> None:
    sequence = (job.events.aggregate(n=Max("sequence"))["n"] or 0) + 1
    JobEvent.objects.create(job=job, sequence=sequence, kind=kind, detail=detail)


def _owned(job: Job, token: UUID) -> bool:
    now = timezone.now()
    return (
        job.state == "running"
        and job.claim_token == token
        and job.lease_until is not None
        and now < job.lease_until
        and now < job.deadline
    )


@transaction.atomic
def enqueue(org_id: int, ticket_id: int) -> Job:
    try:
        ticket = Ticket.objects.select_for_update().get(pk=ticket_id, organization_id=org_id)
    except Ticket.DoesNotExist as exc:
        raise Http404 from exc
    active = ticket.jobs.filter(state__in=["queued", "running"]).first()
    if active:
        return active
    job = Job.objects.create(ticket=ticket, deadline=timezone.now() + timedelta(seconds=120))
    _event(job, "queued", "Fixture suggestion requested; no external reply will be sent.")
    return job


@transaction.atomic
def claim() -> Job | None:
    now = timezone.now()
    candidates = (
        Job.objects.select_for_update(skip_locked=True)
        .filter(Q(state="queued") | Q(state="running", lease_until__lte=now))
        .order_by("pk")
    )
    for job in candidates:
        now = timezone.now()  # Clock is fresh after row lock acquisition.
        if now >= job.deadline or job.attempts >= 2:
            job.state = "expired" if now >= job.deadline else "failed"
            job.error = "Deadline or attempt limit reached."
            job.save(update_fields=["state", "error"])
            _event(job, job.state, job.error)
            continue
        job.state = "running"
        job.claim_token = uuid4()
        job.attempts += 1
        job.lease_until = now + timedelta(seconds=45)
        job.save(update_fields=["state", "claim_token", "attempts", "lease_until"])
        _event(job, "claimed", f"Attempt {job.attempts}; lease 45 seconds.")
        return job
    return None


def execute(job_id: int, token: UUID, provider: Provider | None = None) -> bool:
    with transaction.atomic():
        job = Job.objects.select_for_update().get(pk=job_id)
        if not _owned(job, token):
            return False
        job.guard_reserved += 2000
        job.save(update_fields=["guard_reserved"])
        _event(job, "admitted", "2,000 guard units reserved; not billing or measured usage.")
        ticket = job.ticket
        sources = list(
            Source.objects.filter(organization_id=ticket.organization_id).order_by("pk")[:8]
        )
    result: object = None
    failure = ""
    try:
        result = (provider or suggest)(ticket, sources)
    except Exception as exc:
        failure = f"{type(exc).__name__}: provider transport failed"
    with transaction.atomic():
        job = Job.objects.select_for_update().get(pk=job_id)
        # Validate output only after fresh ownership checks. A stale worker cannot
        # write errors, usage, or suggestions over a reclaimed/cancelled job.
        if not _owned(job, token):
            return False
        try:
            if failure:
                raise ConnectionError(failure)
            fresh_ticket = Ticket.objects.select_for_update().get(
                pk=job.ticket_id, organization_id=ticket.organization_id
            )
            if not _owned(job, token):
                return False
            fresh_sources = list(
                Source.objects.filter(
                    organization_id=fresh_ticket.organization_id, pk__in=[s.pk for s in sources]
                )
            )
            suggestion = validate_suggestion(fresh_ticket, result, fresh_sources)
        except Exception as exc:
            job.error = str(exc)[:500]
            job.state = "queued" if failure and job.attempts < 2 else "failed"
            job.provider_usage = None
            job.save(update_fields=["error", "state", "provider_usage"])
            _event(job, "provider_error", job.error + "; usage unknown")
            return False
        fresh_ticket.revision += 1
        fresh_ticket.save(update_fields=["revision"])
        SuggestionRecord.objects.create(
            revision=fresh_ticket.revision,
            ticket=fresh_ticket,
            job=job,
            category=suggestion["category"],
            reply=suggestion["reply"],
            source_ids=suggestion["source_ids"],
        )
        job.state = "succeeded"
        job.provider_usage = suggestion["usage"]
        job.error = ""
        job.save(update_fields=["state", "provider_usage", "error"])
        _event(
            job,
            "published",
            "Suggestion persisted for human review; usage "
            + ("unknown" if job.provider_usage is None else str(job.provider_usage)),
        )
        return True


@transaction.atomic
def cancel(org_id: int, job_id: int) -> None:
    try:
        job = Job.objects.select_for_update().get(pk=job_id, ticket__organization_id=org_id)
    except Job.DoesNotExist as exc:
        raise Http404 from exc
    if job.state in {"queued", "running"}:
        job.state = "cancelled"
        job.save(update_fields=["state"])
        _event(job, "cancelled", "Cancellation fences any later worker publication.")
