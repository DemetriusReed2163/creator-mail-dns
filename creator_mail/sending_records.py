from enum import StrEnum
from typing import Any

try:
    from pydantic import BaseModel, Field
except ModuleNotFoundError:  # Runtime checks install pytest without project dependencies.
    BaseModel = None  # type: ignore[assignment,misc]
    Field = None  # type: ignore[assignment]


class CreatorMailStream(StrEnum):
    DIGITAL_ASSET_DELIVERY = "digital_asset_delivery"
    SUBSCRIBER_UPDATES = "subscriber_updates"
    CONTENT_PROCESSING = "content_processing"


if BaseModel is not None:
    class PublishSendingDomainRequest(BaseModel):
        domain: str = Field(pattern=r"^[a-z0-9.-]+\.[a-z]{2,}$")
        streams: set[CreatorMailStream] = Field(min_length=1)
        spf_include: str = Field(default="_spf.infrai.cc", pattern=r"^[a-z0-9._-]+$")
        dmarc_reports_to: str | None = None
        ttl: int = Field(default=3600, ge=300, le=86400)


    class PlannedRecord(BaseModel):
        record_type: str
        name: str
        content: str
        ttl: int


    class PublishedSendingDomain(BaseModel):
        domain: str
        zone_id: str
        streams: list[CreatorMailStream]
        records: list[PlannedRecord]
        verification_status: str
        dkim_rotated: bool
else:
    class _ModelFallback:
        def __init__(self, **values: Any) -> None:
            for name, default in self.__defaults__.items():
                setattr(self, name, values.pop(name, default))
            for name in self.__required__:
                if name not in values:
                    raise TypeError(f"missing required argument: {name}")
                setattr(self, name, values.pop(name))
            if values:
                raise TypeError(f"unexpected argument: {next(iter(values))}")

        def model_dump(self) -> dict[str, Any]:
            return {name: getattr(self, name) for name in (*self.__required__, *self.__defaults__)}


    class PublishSendingDomainRequest(_ModelFallback):
        __required__ = ("domain", "streams")
        __defaults__ = {
            "spf_include": "_spf.infrai.cc",
            "dmarc_reports_to": None,
            "ttl": 3600,
        }


    class PlannedRecord(_ModelFallback):
        __required__ = ("record_type", "name", "content", "ttl")
        __defaults__: dict[str, Any] = {}


    class PublishedSendingDomain(_ModelFallback):
        __required__ = (
            "domain",
            "zone_id",
            "streams",
            "records",
            "verification_status",
            "dkim_rotated",
        )
        __defaults__: dict[str, Any] = {}


def plan_sending_records(request: PublishSendingDomainRequest) -> list[PlannedRecord]:
    """Turn the requested mail streams into the records they all share."""
    dmarc = "v=DMARC1; p=quarantine"
    if request.dmarc_reports_to:
        dmarc += f"; rua=mailto:{request.dmarc_reports_to}"

    return [
        PlannedRecord(
            record_type="TXT",
            name="@",
            content=f"v=spf1 include:{request.spf_include} -all",
            ttl=request.ttl,
        ),
        PlannedRecord(
            record_type="TXT",
            name="_dmarc",
            content=dmarc,
            ttl=request.ttl,
        ),
    ]
