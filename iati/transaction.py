# -*- coding: utf-8 -*-
from iati.covidchecks import has_c19_sector, is_c19_narrative


class Transaction:
    def __init__(self, dtransaction):
        self.dtransaction = dtransaction

    def is_strict(self):
        return True if (
            has_c19_sector(self.dtransaction.sectors) or
            (self.dtransaction.description and is_c19_narrative(self.dtransaction.description.narratives))
        ) else False

