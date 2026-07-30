from io import StringIO
import pytest
from django.core.management import call_command
from django.test import override_settings
from support.models import Organization, Ticket


def test_seed_requires_explicit_demo_mode(db):
    with override_settings(DEMO_MODE=False), pytest.raises(Exception, match="DEMO_MODE"):
        call_command("seed_demo")


def test_seed_and_evaluation_are_repeatable(db):
    with override_settings(DEMO_MODE=True):
        call_command("seed_demo")
        count = Ticket.objects.count()
        call_command("seed_demo")
        assert Ticket.objects.count() == count and Organization.objects.count() == 2
        output = StringIO()
        call_command("evaluate", stdout=output)
        assert "6/6" in output.getvalue()
