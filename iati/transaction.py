import logging

from hdx.location.currency import Currency, CurrencyError
from hdx.utilities.dateparse import parse_date

from .calculatesplits import CalculateSplits
from .lookups import Lookups

logger = logging.getLogger(__name__)


class Transaction:
    def __init__(self, transaction_type_info, dtransaction, value):
        """
        Use the get_transaction static method to construct
        """
        self.transaction_type_info = transaction_type_info
        self.dtransaction = dtransaction
        # Use date falling back on value-date
        if dtransaction.date:
            self.date = parse_date(dtransaction.date)
        else:
            self.date = parse_date(dtransaction.value_date)
        self.value = value

    @staticmethod
    def get_transaction(dtransaction, activity_identifier):
        # We're not interested in transactions that have no value
        if not dtransaction.value:
            return None
        # We're only interested in some transaction types
        transaction_type_info = Lookups.configuration["transaction_type_info"].get(
            dtransaction.type
        )
        if not transaction_type_info:
            return None
        # We're not interested in transactions that can't be valued
        try:
            # Use value-date falling back on date
            date = dtransaction.value_date
            if not date:
                date = dtransaction.date
            # Convert the transaction value to USD
            currency = dtransaction.currency
            if currency is None:
                logger.error(
                    f"Activity {activity_identifier} transaction with value {dtransaction.value} currency error!"
                )
                return None
            value = Currency.get_historic_value_in_usd(
                dtransaction.value, currency, parse_date(date)
            )
            if value > Lookups.configuration[
                "usd_error_threshold"
            ] and not Lookups.allow_activity(activity_identifier):
                Lookups.checks.errors_on_exit.add(
                    f"Transaction with value {dtransaction.value} in activity {activity_identifier} is probably an error!"
                )
        except (ValueError, CurrencyError):
            logger.exception(
                f"Activity {activity_identifier} transaction with value {dtransaction.value} USD conversion failed!"
            )
            return None
        return Transaction(transaction_type_info, dtransaction, value)

    def get_label(self):
        return self.transaction_type_info["label"]

    def get_classification(self):
        return self.transaction_type_info["classification"]

    def get_direction(self):
        return self.transaction_type_info["direction"]

    def process(self, today, activity):
        if self.value:
            if (
                Lookups.start_date
                and self.date < Lookups.start_date
            ) or self.date > today:
                # Skip transactions with out-of-range dates
                return False
        else:
            return False

        # Set the net (new money) factors based on the type (commitments or spending)
        self.net_value = self.get_usd_net_value(
            activity.commitment_factor, activity.spending_factor
        )
        # transaction status defaults to activity
        self.is_humanitarian = self.is_humanitarian(activity.humanitarian)
        self.is_strict = self.is_strict(activity)
        return True

    def get_usd_net_value(self, commitment_factor, spending_factor):
        # Set the net (new money) factors based on the type (commitments or spending)
        if self.get_direction() == "outgoing":
            if self.get_classification() == "commitments":
                return self.value * commitment_factor
            else:
                return self.value * spending_factor
        return None

    def is_humanitarian(self, activity_humanitarian):
        transaction_humanitarian = self.dtransaction.humanitarian
        if transaction_humanitarian is None:
            is_humanitarian = activity_humanitarian
        else:
            is_humanitarian = transaction_humanitarian
        return 1 if is_humanitarian else 0

    def is_strict(self, activity):
        try:
            is_strict = (
                True
                if (
                    Lookups.checks.has_desired_sector(self.dtransaction)
                    or (
                        self.dtransaction.description
                        and Lookups.checks.is_desired_narrative(
                            self.dtransaction.description.narratives
                        )
                    )
                )
                else False
            )
        except AttributeError:
            logger.exception(
                f"Activity {activity.identifier} transaction with value {self.dtransaction.value} is_strict call failed!"
            )
            is_strict = False
        is_strict = is_strict or activity.strict
        return 1 if is_strict else 0

    def make_country_or_region_splits(self, activity_country_splits):
        return CalculateSplits.make_country_or_region_splits(
            self.dtransaction, activity_country_splits
        )

    def make_sector_splits(self, activity_sector_splits):
        return CalculateSplits.make_sector_splits(
            self.dtransaction, activity_sector_splits
        )

    def get_provider_receiver(self):
        if self.get_direction() == "incoming":
            provider = Lookups.get_org_info(self.dtransaction.provider_org)
            receiver = {"id": "", "name": "", "type": ""}
        else:
            provider = {"id": "", "name": "", "type": ""}
            expenditure = self.get_label() == "Expenditure"
            receiver = Lookups.get_org_info(
                self.dtransaction.receiver_org, expenditure=expenditure
            )
        return provider, receiver
