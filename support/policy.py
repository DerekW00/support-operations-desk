from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True)
class SLAPolicy:
    deadline: datetime
    escalated: bool


def compute_sla(tier: str, outage_verified: bool, received_at: datetime) -> SLAPolicy:
    if tier not in {"standard", "priority"} or received_at.utcoffset() is None:
        raise ValueError("Known tier and aware received time required")
    hours = 1 if outage_verified else (4 if tier == "priority" else 24)
    return SLAPolicy(received_at + timedelta(hours=hours), outage_verified)
