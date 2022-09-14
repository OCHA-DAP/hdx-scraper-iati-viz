from .flatten import flatten


class SmallDTransaction:
    __slots__ = [
        "type",
        "transaction_date",
        "currency",
        "valuation_date",
        "value",
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
        self.transaction_date = dtransaction.transaction_date
        self.currency = dtransaction.currency
        self.valuation_date = dtransaction.valuation_date
        self.value = dtransaction.value
        self.humanitarian = dtransaction.humanitarian
        self.sectors = flatten(dtransaction.sectors)
        self.description = flatten(dtransaction.description)
        self.provider_org = flatten(dtransaction.provider_org)
        self.receiver_org = flatten(dtransaction.receiver_org)
        self.recipient_countries = flatten(dtransaction.recipient_countries)
        self.recipient_regions = flatten(dtransaction.recipient_regions)
