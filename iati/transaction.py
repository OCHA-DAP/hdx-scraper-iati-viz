# -*- coding: utf-8 -*-
from iati.calculatesplits import CalculateSplits
from iati.covidchecks import has_c19_sector, is_c19_narrative
from iati.lookups import Lookups


class Transaction:
    def __init__(self, configuration, this_month, dtransaction):
        self.this_month = this_month
        self.dtransaction = dtransaction
        self.transaction_type_info = configuration['transaction_type_info'].get(dtransaction.type)
        self.value = None
        self.month = None

    def is_strict(self):
        return True if (
            has_c19_sector(self.dtransaction.sectors) or
            (self.dtransaction.description and is_c19_narrative(self.dtransaction.description.narratives))
        ) else False

    def should_process(self):
        self.month = self.dtransaction.date[:7]
        if self.month < '2020-01' or self.month > self.this_month or not self.dtransaction.value:
            # Skip transactions with no values or with out-of-range months
            return False

        if self.transaction_type_info is None:
            # skip transaction types that don't interest us
            return False
        return True

    def get_month(self):
        return self.month

    def get_classification_direction(self):
        return self.transaction_type_info['classification'], self.transaction_type_info['direction']

    def calculate_value(self):
        # Convert the transaction value to USD
        self.value = Lookups.get_value_in_usd(self.dtransaction.value, self.dtransaction.currency, self.dtransaction.date)
        return self.value

    def get_net_value(self, commitment_factor, spending_factor):
        # Set the net (new money) factors based on the type (commitments or spending)
        if self.transaction_type_info['direction'] == 'outgoing':
            if self.transaction_type_info['classification'] == 'commitments':
                return self.value * commitment_factor
            else:
                return self.value * spending_factor
        return None

    def humanitarian(self):
        return self.dtransaction.humanitarian

    def make_country_splits(self, activity_country_splits):
        return CalculateSplits.make_country_splits(self.dtransaction, activity_country_splits)

    def make_sector_splits(self, activity_sector_splits):
        return CalculateSplits.make_sector_splits(self.dtransaction, activity_sector_splits)

    def get_provider_receiver(self):
        if self.transaction_type_info['direction'] == 'incoming':
            provider = Lookups.get_org_name(self.dtransaction.provider_org)
            receiver = None
        else:
            provider = None
            receiver = Lookups.get_org_name(self.dtransaction.receiver_org)
        return provider, receiver
