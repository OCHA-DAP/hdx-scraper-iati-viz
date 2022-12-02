from .flatten import flatten
from .lookups import Lookups


class SmallDTransaction:
    __slots__ = [
        "date",
        "type",
        "value_date",
        "currency",
        "value",
        "humanitarian",
        "sectors",
        "is_strict",
        "provider_org",
        "receiver_org",
        "recipient_countries",
        "recipient_regions",
        "should_skip_transaction",
    ]

    def __init__(self, dtransaction, transaction_is_strict, should_skip_transaction):
        self.date = dtransaction.date
        self.type = dtransaction.type
        self.value_date = dtransaction.value_date
        self.currency = dtransaction.currency
        self.value = dtransaction.value
        self.humanitarian = dtransaction.humanitarian
        self.sectors = flatten(dtransaction.sectors)
        self.is_strict = transaction_is_strict
        self.provider_org = flatten(dtransaction.provider_org)
        self.receiver_org = flatten(dtransaction.receiver_org)
        self.recipient_countries = flatten(dtransaction.recipient_countries)
        self.recipient_regions = flatten(dtransaction.recipient_regions)
        self.should_skip_transaction = should_skip_transaction


def get_transaction_is_strict(dactivity, activity_is_strict, dtransaction):
    try:
        is_strict = (
            True
            if (
                Lookups.checks.has_desired_sector(dtransaction)
                or (
                    dtransaction.description
                    and Lookups.checks.is_desired_narrative(
                        dtransaction.description.narratives
                    )
                )
            )
            else False
        )
    except AttributeError:
        Lookups.checks.errors_on_exit.add(
            f"Activity {dactivity.identifier} transaction with usd value {dtransaction.usd_value} is_strict call failed!"
        )
        is_strict = False
    is_strict = is_strict or activity_is_strict
    return 1 if is_strict else 0


def create_small_transaction(dactivity, activity_is_strict, dtransaction):
    transaction_is_strict = get_transaction_is_strict(
        dactivity, activity_is_strict, dtransaction
    )
    should_skip_transaction = Lookups.checks.should_skip_transaction(
        dactivity, dtransaction
    )
    return SmallDTransaction(
        dtransaction, transaction_is_strict, should_skip_transaction
    )
