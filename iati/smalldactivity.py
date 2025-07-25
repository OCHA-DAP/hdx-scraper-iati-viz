from .lookups import Lookups
from .smalldtransaction import create_small_transaction
from .utilities import flatten


class SmallDActivity:
    __slots__ = [
        "identifier",
        "reporting_org",
        "sectors",
        "humanitarian",
        "recipient_countries",
        "recipient_regions",
        "participating_orgs",
        "participating_orgs_by_role",
        "transactions",
    ]

    def __init__(self, dactivity, activity_is_strict):
        self.identifier = dactivity.identifier
        self.reporting_org = flatten(dactivity.reporting_org)
        self.sectors = flatten(dactivity.sectors)
        self.humanitarian = dactivity.humanitarian
        self.recipient_countries = flatten(dactivity.recipient_countries)
        self.recipient_regions = flatten(dactivity.recipient_regions)
        self.participating_orgs = flatten(dactivity.participating_orgs)
        self.participating_orgs_by_role = flatten(dactivity.participating_orgs_by_role)
        self.transactions = [
            create_small_transaction(dactivity, activity_is_strict, dtransaction)
            for dtransaction in dactivity.transactions
        ]


def create_small_dactivity(dactivity):
    activity_is_strict = Lookups.checks.get_activity_is_strict(dactivity)
    return SmallDActivity(dactivity, activity_is_strict)
