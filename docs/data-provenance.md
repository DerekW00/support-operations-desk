# Data provenance

All account names, organization names, customer messages, outages, source excerpts and provider results are newly synthetic and created for this local demonstration. They describe no actual person, customer, incident or service. No employer material or private data was used.

support/management/commands/seed_demo.py is the reproducible source of the domain examples. support/fixtures/provider.json freezes six provider response classes. The provider makes no network call. The second tenant is deliberately seeded with separate account, ticket and source records for isolation checks.

The six scripted functional cases check contract behavior: ordinary ambiguity, verified outage, transport failure, malformed output, unsupported promise and missing usage. Their pass count is not measured live-model accuracy, quality, speed or cost.

HTMX 2.0.8 was retrieved from its versioned npm distribution at https://unpkg.com/htmx.org@2.0.8/dist/htmx.min.js; the upstream license came from https://github.com/bigskysoftware/htmx/blob/v2.0.8/LICENSE. No remote fonts, images or external UI assets are used.
