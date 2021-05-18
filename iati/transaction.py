# -*- coding: utf-8 -*-
from iati.covidchecks import has_c19_sector, is_c19_narrative
from iati.utils import convert_to_usd


class Transaction:
    def __init__(self, configuration, this_month, dtransaction):
        self.transaction_type_info = configuration['transaction_type_info']
        self.this_month = this_month
        self.dtransaction = dtransaction
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

        if self.dtransaction.type not in self.transaction_type_info:
            # skip transaction types that don't interest us
            return False
        return True

    def get_month(self):
        return self.month

    def get_type_info(self):
        return self.transaction_type_info[self.dtransaction.type]

    def calculate_value(self):
        # Convert the transaction value to USD
        self.value = convert_to_usd(self.dtransaction.value, self.dtransaction.currency, self.dtransaction.date)
        return self.value

    def get_net_value(self, commitment_factor, spending_factor):
        type_info = self.get_type_info()
        # Set the net (new money) factors based on the type (commitments or spending)
        if type_info['direction'] == 'outgoing':
            if type_info['classification'] == 'commitments':
                return self.value * commitment_factor
            else:
                return self.value * spending_factor
        return None
