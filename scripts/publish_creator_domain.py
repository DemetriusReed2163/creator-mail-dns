import argparse
import asyncio
import json
import os

from creator_mail.domain_publisher import publish_sending_domain
from creator_mail.infrai_client import InfraiClient
from creator_mail.sending_records import CreatorMailStream, PublishSendingDomainRequest


async def run(domain: str, reports_to: str | None) -> None:
    api_key = os.environ["INFRAI_API_KEY"]
    request = PublishSendingDomainRequest(
        domain=domain,
        streams=set(CreatorMailStream),
        dmarc_reports_to=reports_to,
    )
    async with InfraiClient(api_key=api_key) as client:
        result = await publish_sending_domain(request, client)
    print(json.dumps(result.model_dump(mode="json"), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Publish a creator sending domain")
    parser.add_argument("domain")
    parser.add_argument("--reports-to")
    args = parser.parse_args()
    asyncio.run(run(args.domain, args.reports_to))
