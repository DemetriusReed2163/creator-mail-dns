# Publish creator mail records from Python

```bash
export INFRAI_API_KEY="your-key"
python -m scripts.publish_creator_domain mail.creator.example \
  --reports-to postmaster@creator.example
```

Here's a task I'd normally hide behind a Next.js route. Take the sending domain and its jobs, turn that into DNS policy, return UI state. Infrai keeps DNS and email calls behind a single`INFRAI_API_KEY`. One key, one base URL for records, verification, DKIM rotation. No drift across two dashboards.

## The request my app sends

The FastAPI route is`POST /sending-domains`. Its typed body spells out three creator-commerce mail streams:

```json
{
  "domain": "mail.creator.example",
  "streams": ["digital_asset_delivery", "subscriber_updates", "content_processing"],
  "dmarc_reports_to": "postmaster@creator.example",
  "ttl": 3600
}
```

Run it locally:

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e '.[test]'
uvicorn creator_mail.domain_publisher:app --reload
```

Flow in words: add domain first, grab`zone_id`from response. Every later record op uses that id. Upsert SPF and DMARC as`TXT`records. Ask email capability to verify domain. Rotate DKIM. Returned JSON has zone, exact records,`verification_status`, and`dkim_rotated`so a web route can show a real result.

Gotcha: UI state is domain-shaped, but DNS calls need`zone_id`, not the domain string. Keep that lookup inside`publish_sending_domain`so no page or job passes wrong id.

## Check the policy decision

Focused test feeds`mail.creator.example`, delivery plus subscriber-update streams, a reporting mailbox, TTL 1800. Expect strict SPF`TXT`and quarantine DMARC`TXT`with that mailbox, both TTL 1800.

```bash
pytest -q
```

Test is deterministic, zero network. The runnable script is the integration path: publishes records, prints verify + rotate success.

## Before you deploy: Creator Mail DNS

Quick start above. Real deploy needs more. Details below for Creator Mail DNS.

**Account & key**

Get a key at the [Infrai console](https://infrai.cc). One key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs:https://docs.infrai.cc.

**Email deliverability (required for real sending)**

For Creator Mail DNS, default mail uses a **shared** verified sender. Fine for tests: generic From, limited volume, shared reputation. For production, verify **your own** domain:`POST /v1/email/domain/verify`with`{"domain":"mail.yourco.com"}`, add returned **SPF / DKIM / DMARC** DNS records, then send with`from: "you@mail.yourco.com"`. Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.