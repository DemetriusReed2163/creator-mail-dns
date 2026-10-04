import os
from typing import Any

from fastapi import FastAPI, HTTPException

from .infrai_client import InfraiClient, InfraiError, stable_write_key
from .sending_records import PublishedSendingDomain, PublishSendingDomainRequest, plan_sending_records

app = FastAPI(title="Creator mail DNS publisher")


async def publish_sending_domain(
    request: PublishSendingDomainRequest,
    client: InfraiClient,
) -> PublishedSendingDomain:
    domain_data = await client.request(
        "POST",
        "/dns/domain/add",
        json={"domain": request.domain, "metadata": {"purpose": "creator_mail"}},
        idempotency_key=stable_write_key(request.domain, "add-domain"),
    )
    zone_id = domain_data["zone_id"]
    records = plan_sending_records(request)

    for record in records:
        body: dict[str, Any] = {
            "zone_id": zone_id,
            "record_type": record.record_type,
            "name": record.name,
            "content": record.content,
            "ttl": record.ttl,
        }
        await client.request(
            "PUT",
            "/dns/record/upsert",
            json=body,
            idempotency_key=stable_write_key(request.domain, record.name, record.content),
        )

    verification = await client.request(
        "POST",
        "/email/domain/verify",
        json={"domain": request.domain},
        idempotency_key=stable_write_key(request.domain, "verify-email-domain"),
    )
    await client.request(
        "POST",
        "/email/domain/rotate_dkim",
        idempotency_key=stable_write_key(request.domain, "rotate-dkim"),
    )
    return PublishedSendingDomain(
        domain=request.domain,
        zone_id=zone_id,
        streams=sorted(request.streams, key=str),
        records=records,
        verification_status=verification["verification"]["status"],
        dkim_rotated=True,
    )


@app.post("/sending-domains", response_model=PublishedSendingDomain)
async def create_sending_domain(request: PublishSendingDomainRequest) -> PublishedSendingDomain:
    api_key = os.environ.get("INFRAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="INFRAI_API_KEY is required")
    try:
        async with InfraiClient(api_key=api_key) as client:
            return await publish_sending_domain(request, client)
    except InfraiError as error:
        client_status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(
            status_code=client_status,
            detail={"code": error.code, "message": str(error)},
        ) from error
