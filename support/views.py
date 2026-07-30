import json
from django.contrib.auth.decorators import login_required
from typing import cast
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from support.forms import ImportForm, ReviewForm
from support.ingestion import ImportConflict, InvalidImport, TicketInput, ingest_bulk
from support.jobs import cancel, enqueue
from support.models import Account, Job, Membership, Organization, Source, Ticket
from support.provider import InvalidSuggestion
from support.reviews import ReviewConflict, save_review


def organization(request: HttpRequest) -> Organization:
    try:
        return (
            Membership.objects.select_related("organization")
            .get(user_id=cast(int, request.user.pk))
            .organization
        )
    except Membership.DoesNotExist as exc:
        raise Http404 from exc


@login_required
def queue(request: HttpRequest) -> HttpResponse:
    org = organization(request)
    tickets = (
        Ticket.objects.filter(organization=org)
        .select_related("account")
        .order_by("-escalated", "deadline")
    )
    return render(
        request,
        "support/queue.html",
        {
            "org": org,
            "tickets": tickets,
            "urgent": tickets.filter(escalated=True).count(),
            "total": tickets.count(),
        },
    )


def _detail(
    request: HttpRequest,
    ticket: Ticket,
    form: ReviewForm | None = None,
    error: str = "",
    status: int = 200,
) -> HttpResponse:
    review = ticket.reviews.first()
    suggestion = ticket.suggestions.first()
    if form is None:
        initial = review or suggestion
        form = ReviewForm(
            initial={
                "expected_revision": ticket.revision,
                "category": initial.category if initial else "uncertain",
                "reply": initial.reply if initial else "",
            }
        )
    citations = Source.objects.filter(
        organization=ticket.organization, pk__in=suggestion.source_ids if suggestion else []
    )
    return render(
        request,
        "support/detail.html",
        {
            "ticket": ticket,
            "form": form,
            "review": review,
            "suggestion": suggestion,
            "citations": citations,
            "history": ticket.reviews.select_related("actor"),
            "job": ticket.jobs.order_by("-pk").first(),
            "error": error,
            "now": timezone.now(),
        },
        status=status,
    )


@login_required
def detail(request: HttpRequest, ticket_id: int) -> HttpResponse:
    ticket = get_object_or_404(Ticket, pk=ticket_id, organization=organization(request))
    return _detail(request, ticket)


@login_required
@require_POST
def review(request: HttpRequest, ticket_id: int) -> HttpResponse:
    org = organization(request)
    ticket = get_object_or_404(Ticket, pk=ticket_id, organization=org)
    form = ReviewForm(request.POST)
    if not form.is_valid():
        return _detail(request, ticket, form, "Correct the highlighted fields.", 400)
    try:
        save_review(
            org.pk,
            ticket.pk,
            cast(int, request.user.pk),
            form.cleaned_data["expected_revision"],
            form.cleaned_data["category"],
            form.cleaned_data["reply"],
            request.POST.get("action") == "approve",
        )
    except ReviewConflict as exc:
        return _detail(request, ticket, form, str(exc), 409)
    except InvalidSuggestion as exc:
        return _detail(request, ticket, form, str(exc), 400)
    return redirect("detail", ticket_id=ticket.pk)


@login_required
@require_POST
def generate(request: HttpRequest, ticket_id: int) -> HttpResponse:
    org = organization(request)
    get_object_or_404(Ticket, pk=ticket_id, organization=org)
    enqueue(org.pk, ticket_id)
    return redirect("detail", ticket_id=ticket_id)


@login_required
@require_POST
def cancel_job(request: HttpRequest, job_id: int) -> HttpResponse:
    org = organization(request)
    job = get_object_or_404(Job, pk=job_id, ticket__organization=org)
    cancel(org.pk, job.pk)
    return redirect("detail", ticket_id=job.ticket_id)


@login_required
def job_status(request: HttpRequest, job_id: int) -> HttpResponse:
    job = get_object_or_404(Job, pk=job_id, ticket__organization=organization(request))
    return render(request, "support/job.html", {"job": job, "now": timezone.now()})


@login_required
def source(request: HttpRequest, source_id: int) -> HttpResponse:
    source = get_object_or_404(Source, pk=source_id, organization=organization(request))
    return render(request, "support/source.html", {"source": source})


@login_required
def import_tickets(request: HttpRequest) -> HttpResponse:
    org = organization(request)
    raw_size = len(request.body) if request.method == "POST" else 0
    form = ImportForm(request.POST or None)
    error = ""
    if request.method == "POST" and form.is_valid():
        try:
            data = json.loads(form.cleaned_data["tickets"])
            if not isinstance(data, list):
                raise InvalidImport("Expected an array of ticket objects.")
            if len(data) > 50:
                raise InvalidImport("Imports allow at most 50 tickets.")
            events = [TicketInput(**row) for row in data]
            ingest_bulk(org.pk, events, raw_size=raw_size)
            return redirect("queue")
        except (json.JSONDecodeError, TypeError, InvalidImport, ImportConflict) as exc:
            error = str(exc)
    return render(
        request,
        "support/import.html",
        {"form": form, "error": error, "accounts": Account.objects.filter(organization=org)},
        status=400 if error else 200,
    )
