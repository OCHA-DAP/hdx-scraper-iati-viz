import logging

from hdx.utilities.dateparse import parse_date

from .calculatesplits import CalculateSplits
from .lookups import Lookups

logger = logging.getLogger(__name__)


class Transaction:
    def __init__(self, transaction_type_info, dtransaction, activity):
        """
        Use the get_transaction static method to construct
        """
        self.transaction_type_info = transaction_type_info
        self.dtransaction = dtransaction
        self.date = parse_date(dtransaction.usddate)
        self.value = dtransaction.usdvalue
        # transaction status defaults to activity
        self.is_humanitarian = self.is_humanitarian(activity.humanitarian)
        self.is_strict = self.is_strict(activity)
        self.net_value = None

    def get_label(self):
        return self.transaction_type_info["label"]

    def get_classification(self):
        return self.transaction_type_info["classification"]

    def get_direction(self):
        return self.transaction_type_info["direction"]

    def calculate_net_value(self, activity):
        # Set the net (new money) factors based on the type (commitments or spending)
        if self.get_direction() == "outgoing":
            if self.get_classification() == "commitments":
                self.net_value = self.value * activity.commitment_factor
            else:
                self.net_value = self.value * activity.spending_factor

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
