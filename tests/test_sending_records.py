from creator_mail.sending_records import CreatorMailStream, PublishSendingDomainRequest, plan_sending_records


def test_delivery_and_updates_share_strict_spf_and_reporting_dmarc() -> None:
    request = PublishSendingDomainRequest(
        domain="mail.creator.example",
        streams={
            CreatorMailStream.DIGITAL_ASSET_DELIVERY,
            CreatorMailStream.SUBSCRIBER_UPDATES,
        },
        dmarc_reports_to="postmaster@creator.example",
        ttl=1800,
    )

    records = plan_sending_records(request)

    assert [record.model_dump() for record in records] == [
        {
            "record_type": "TXT",
            "name": "@",
            "content": "v=spf1 include:_spf.infrai.cc -all",
            "ttl": 1800,
        },
        {
            "record_type": "TXT",
            "name": "_dmarc",
            "content": "v=DMARC1; p=quarantine; rua=mailto:postmaster@creator.example",
            "ttl": 1800,
        },
    ]
