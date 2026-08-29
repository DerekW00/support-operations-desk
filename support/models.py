import uuid
from django.conf import settings
from django.db import models
from django.utils import timezone


class Organization(models.Model):
    name = models.CharField(max_length=100)


class Membership(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class Account(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    tier = models.CharField(
        max_length=20, choices=[("standard", "Standard"), ("priority", "Priority")]
    )


class Outage(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.CASCADE)
    verified = models.BooleanField(default=False)
    title = models.CharField(max_length=150)
    active = models.BooleanField(default=True)


class Source(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    title = models.CharField(max_length=150)
    body = models.TextField()


class Ticket(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    account = models.ForeignKey(Account, on_delete=models.PROTECT)
    event_id = models.CharField(max_length=100)
    payload_hash = models.CharField(max_length=64)
    subject = models.CharField(max_length=160)
    customer_text = models.TextField()
    received_at = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField()
    escalated = models.BooleanField(default=False)
    revision = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["organization", "event_id"], name="ticket_org_event")
        ]


class Review(models.Model):
    basis_suggestion = models.ForeignKey(
        "SuggestionRecord", null=True, on_delete=models.PROTECT, related_name="based_reviews"
    )
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="reviews")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    revision = models.PositiveIntegerField()
    category = models.CharField(max_length=30)
    reply = models.TextField()
    approved = models.BooleanField(default=False)
    source_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["ticket", "revision"], name="review_ticket_revision")
        ]
        ordering = ["-revision"]


class SuggestionRecord(models.Model):
    revision = models.PositiveIntegerField(default=0)
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="suggestions")
    job = models.OneToOneField("Job", on_delete=models.PROTECT)
    category = models.CharField(max_length=30)
    reply = models.TextField()
    source_ids = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-pk"]


class Job(models.Model):
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT, related_name="jobs")
    state = models.CharField(max_length=20, default="queued")
    created_at = models.DateTimeField(default=timezone.now)
    deadline = models.DateTimeField()
    lease_until = models.DateTimeField(null=True)
    claim_token = models.UUIDField(default=uuid.uuid4)
    attempts = models.PositiveIntegerField(default=0)
    guard_reserved = models.PositiveIntegerField(default=0)
    provider_usage = models.PositiveIntegerField(null=True)
    error = models.TextField(blank=True)


class JobEvent(models.Model):
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="events")
    sequence = models.PositiveIntegerField()
    kind = models.CharField(max_length=50)
    detail = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["sequence"]
        constraints = [
            models.UniqueConstraint(fields=["job", "sequence"], name="job_event_sequence")
        ]
