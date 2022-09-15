from .flatten import flatten


class SmallDTransaction:
    __slots__ = [
        "type",
        "aid_types",
        "transaction_date",
        "usd_value",
        "humanitarian",
        "sectors",
        "description",
        "provider_org",
        "receiver_org",
        "recipient_countries",
        "recipient_regions",
    ]

    def __init__(self, dtransaction):
        self.type = dtransaction.type
        self.aid_types = dtransaction.aid_types
        self.transaction_date = dtransaction.transaction_date
        self.usd_value = dtransaction.usd_value
        self.humanitarian = dtransaction.humanitarian
        self.sectors = flatten(dtransaction.sectors)
        self.description = flatten(dtransaction.description)
        self.provider_org = flatten(dtransaction.provider_org)
        self.receiver_org = flatten(dtransaction.receiver_org)
        self.recipient_countries = flatten(dtransaction.recipient_countries)
        self.recipient_regions = flatten(dtransaction.recipient_regions)
