import pytest
from django.contrib.auth.models import User
from support.models import Organization, Membership, Account, Source


@pytest.fixture
def domain(db):
    org = Organization.objects.create(name="Northstar")
    other = Organization.objects.create(name="Other")
    user = User.objects.create_user("reviewer", password="test-password")
    Membership.objects.create(organization=org, user=user)
    account = Account.objects.create(organization=org, name="Birch", tier="priority")
    source = Source.objects.create(
        organization=org, title="Availability", body="We are investigating service availability."
    )
    return org, other, user, account, source
