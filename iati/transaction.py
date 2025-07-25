import logging

from hdx.utilities.dateparse import parse_date

from .calculatesplits import CalculateSplits
from .lookups import Lookups

logger = logging.getLogger(__name__)


class Transaction:
    def __init__(self, dtransaction):
        """
        Use the get_transaction static method to construct
        """
        self.dtransaction = dtransaction
        self.transaction_type_info = Lookups.configuration["transaction_type_info"][
            dtransaction.type
        ]
        self.transaction_date = dtransaction.transaction_date
        self.valuation_date = dtransaction.valuation_date
        self.usd_value = dtransaction.value
        self.is_strict = dtransaction.is_strict

    def get_label(self):
        return self.transaction_type_info["label"]

    def get_classification(self):
        return self.transaction_type_info["classification"]

    def get_direction(self):
        return self.transaction_type_info["direction"]

    def skip(self):
        return self.dtransaction.should_skip_transaction

    def process(self, activity):
        # Set the net (new money) factors based on the type (commitments or spending)
        self.net_value = self.get_usd_net_value(
            activity.commitment_factor, activity.spending_factor
        )
        # transaction status defaults to activity
        self.is_humanitarian = self.is_humanitarian(activity.humanitarian)

    def get_usd_net_value(self, commitment_factor, spending_factor):
        # Set the net (new money) factors based on the type (commitments or spending)
        if self.get_direction() == "outgoing":
            if self.get_classification() == "commitments":
                return self.usd_value * commitment_factor
            else:
                return self.usd_value * spending_factor
        return None

    def is_humanitarian(self, activity_humanitarian):
        transaction_humanitarian = self.dtransaction.humanitarian
        if transaction_humanitarian is None:
            is_humanitarian = activity_humanitarian
        else:
            is_humanitarian = transaction_humanitarian
        return 1 if is_humanitarian else 0

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
