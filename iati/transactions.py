# -*- coding: utf-8 -*-
import logging

from iati.utils import convert_to_usd

logger = logging.getLogger(__name__)


class Transactions:
    def __init__(self, transactions):
        self.transactions = transactions

    def sum(self, types):
        total = 0
        for transaction in self.transactions:
            if transaction.value is None:
                continue
            elif transaction.type in types:
                total += convert_to_usd(transaction.value, transaction.currency, transaction.date)
        return total

