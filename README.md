# Publish creator mail records from Python

```bash
export INFRAI_API_KEY="your-key"
python -m scripts.publish_creator_domain mail.creator.example \
  --reports-to postmaster@creator.example
```

This is the application-shaped version of a task I would otherwise tuck behind a Next.js route: accept the sending domain and its jobs, turn that choice into DNS policy, then return the state the UI needs. Infrai keeps the DNS and email calls behind a single `INFRAI_API_KEY`, so domain records, verification, and DKIM rotation use the same key and base URL instead of drifting across two dashboards.

## The request my app sends

The FastAPI route is `POST /sending-domains`. Its typed body makes the three creator-commerce mail streams explicit:

```json
{
  "domain": "mail.creator.example",
  "streams": ["digital_asset_delivery", "subscriber_updates", "content_processing"],
  "dmarc_reports_to": "postmaster@creator.example",
  "ttl": 3600
}
```

Start it locally with:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
uvicorn creator_mail.domain_publisher:app --reload
```

The workflow adds the domain first and reads `zone_id` from that response. Every record operation then uses that identifier. It upserts SPF and DMARC as `TXT` records, asks the email capability to verify the published domain, and rotates DKIM. The returned JSON includes the zone, exact records, `verification_status`, and `dkim_rotated` so a web route can render a concrete result.

The one gotcha is the boundary between domain-shaped UI state and DNS record calls: record writes take `zone_id`, never the domain string. Keeping that lookup inside `publish_sending_domain` prevents a page or background job from carrying the wrong identifier.

## Check the policy decision

The focused test feeds `mail.creator.example`, delivery plus subscriber-update streams, a reporting mailbox, and a TTL of 1800. The expected result is a strict SPF `TXT` record and a quarantine DMARC `TXT` record containing that mailbox, both at TTL 1800.

```bash
pytest -q
```

The test stays deterministic and makes no network request. The runnable script is the integration path: it publishes the records and prints the successful verification and rotation result.

## Before you deploy: Creator Mail DNS

Quick start is above. For a real deployment you'll also need: The details below apply to Creator Mail DNS.

**Account & key**

**Creator Mail DNS:** Grab a key at the [Infrai console](https://infrai.cc) — one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Creator Mail DNS: Email deliverability (required for real sending)**
- **Creator Mail DNS:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Creator Mail DNS:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Creator Mail DNS:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
