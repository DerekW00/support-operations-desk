import json
import re
from pathlib import Path
from typing import TypedDict, cast
from support.models import Ticket, Source

CATEGORIES = ("technical", "billing", "account", "uncertain")


class InvalidSuggestion(ValueError):
    pass


class Suggestion(TypedDict):
    category: str
    reply: str
    source_ids: list[int]
    usage: int | None


def validate_reply(category: str, reply: str) -> None:
    if (
        category not in CATEGORIES
        or not isinstance(reply, str)
        or not reply.strip()
        or len(reply) > 4000
    ):
        raise InvalidSuggestion("Select an approved category and a reply of 1–4,000 characters.")
    if re.search(
        r"\b(refund|credit|guarantee\w*|tomorrow|within\s+\d+|by\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|in\s+\d+\s+(?:hours?|minutes?|days?))\b",
        reply,
        re.I,
    ):
        raise InvalidSuggestion(
            "Unsupported financial or guaranteed timing promise. Remove it before saving."
        )


def validate_suggestion(ticket: Ticket, result: object, sources: list[Source]) -> Suggestion:
    if not isinstance(result, dict) or set(result) != {"category", "reply", "source_ids", "usage"}:
        raise InvalidSuggestion("Provider response has missing or unexpected fields.")
    category, reply, ids, usage = (
        result[key] for key in ("category", "reply", "source_ids", "usage")
    )
    validate_reply(category, reply)
    allowed = {s.pk for s in sources if s.organization_id == ticket.organization_id}
    if (
        not isinstance(ids, list)
        or not ids
        or len(ids) > 8
        or any(type(i) is not int or i not in allowed for i in ids)
        or len(set(ids)) != len(ids)
    ):
        raise InvalidSuggestion("Provider must cite available organization-owned sources.")
    if usage is not None and (type(usage) is not int or usage < 0 or usage > 2000):
        raise InvalidSuggestion("Provider usage is malformed or exceeds the admitted guard.")
    return cast(
        Suggestion, {"category": category, "reply": reply, "source_ids": ids, "usage": usage}
    )


def suggest(ticket: Ticket, sources: list[Source]) -> Suggestion:
    # The fixture never executes customer instructions or makes a network call.
    fixtures = json.loads((Path(__file__).parent / "fixtures/provider.json").read_text())
    key = "outage" if ticket.escalated else "ambiguous"
    for marker, name in [
        ("[transport-error]", "transport"),
        ("[malformed]", "malformed"),
        ("[promise]", "promise"),
        ("[missing-usage]", "missing_usage"),
    ]:
        if marker in ticket.customer_text:
            key = name
    response = fixtures[key]
    if key == "transport":
        raise ConnectionError(response["error"])
    result = dict(response)
    if "source_ids" in result:
        result["source_ids"] = [s.pk for s in sources[:1]]
    return cast(Suggestion, result)
