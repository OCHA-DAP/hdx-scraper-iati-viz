from .flatten import flatten
from .lookups import Lookups
from .smalldtransaction import create_small_transaction


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

    def __init__(self, dactivity, activity_is_strict, removed_transactions):
        self.identifier = dactivity.identifier
        self.reporting_org = flatten(dactivity.reporting_org)
        self.sectors = flatten(dactivity.sectors)
        self.humanitarian = dactivity.humanitarian
        self.recipient_countries = flatten(dactivity.recipient_countries)
        self.recipient_regions = flatten(dactivity.recipient_regions)
        self.participating_orgs = flatten(dactivity.participating_orgs)
        self.participating_orgs_by_role = flatten(dactivity.participating_orgs_by_role)
        self.transactions = [
            create_small_transaction(self.identifier, activity_is_strict, dtransaction)
            for i, dtransaction in enumerate(dactivity.transactions)
            if i not in removed_transactions
        ]


def get_activity_is_strict(dactivity):
    try:
        return (
            True
            if (
                Lookups.checks.has_desired_scope(dactivity)
                or Lookups.checks.has_desired_marker(dactivity)
                or Lookups.checks.has_desired_tag(dactivity)
                or Lookups.checks.has_desired_sector(dactivity)
                or Lookups.checks.is_desired_narrative(dactivity.title.narratives)
            )
            else False
        )
    except AttributeError:
        Lookups.checks.errors_on_exit.add(
            f"Activity {dactivity.identifier} is_strict call failed!"
        )
        return False


def create_small_dactivity(dactivity, removed_transactions):
    activity_is_strict = get_activity_is_strict(dactivity)
    return SmallDActivity(dactivity, activity_is_strict, removed_transactions)
