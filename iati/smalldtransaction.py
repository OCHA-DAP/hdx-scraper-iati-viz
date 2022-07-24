from .flatten import flatten


class SmallDTransaction:
    __slots__ = [
        "value",
        "type",
        "value_date",
        "date",
        "currency",
        "humanitarian",
        "sectors",
        "description",
        "provider_org",
        "receiver_org",
        "recipient_countries",
        "recipient_regions",
    ]

    def __init__(self, dtransaction):
        self.value = dtransaction.value
        self.type = dtransaction.type
        self.value_date = dtransaction.value_date
        self.date = dtransaction.date
        self.currency = dtransaction.currency
        self.humanitarian = dtransaction.humanitarian
        self.sectors = flatten(dtransaction.sectors)
        self.description = flatten(dtransaction.description)
        self.provider_org = flatten(dtransaction.provider_org)
        self.receiver_org = flatten(dtransaction.receiver_org)
        self.recipient_countries = flatten(dtransaction.recipient_countries)
        self.recipient_regions = flatten(dtransaction.recipient_regions)
