import json
from django.test import Client
from support.models import Ticket


def test_valid_http_import_is_atomic_and_redirects(domain):
    _, _, user, account, _ = domain
    client = Client()
    client.force_login(user)
    payload = [
        {"event_id": "http-1", "account_id": account.pk, "subject": "Help", "text": "A question."}
    ]
    response = client.post("/import/", {"tickets": json.dumps(payload)})
    assert response.status_code == 302
    assert Ticket.objects.get(event_id="http-1").customer_text == "A question."
