from datetime import datetime, timedelta, timezone
import pytest
from support.policy import compute_sla


@pytest.mark.parametrize(
    "tier,outage,hours,escalated",
    [("standard", False, 24, False), ("priority", False, 4, False), ("standard", True, 1, True)],
)
def test_only_verified_policy_controls_deadline(tier, outage, hours, escalated):
    at = datetime(2026, 10, 26, 12, tzinfo=timezone.utc)
    result = compute_sla(tier, outage, at)
    assert result.deadline == at + timedelta(hours=hours)
    assert result.escalated is escalated
