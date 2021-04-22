# -*- coding: utf-8 -*-
import logging
from datetime import datetime

from hdx.utilities.loader import load_json

from iati.transactions import Transactions
from iati.utils import clean_string, pack_key, convert_to_usd

logger = logging.getLogger(__name__)


class Activities:
    def __init__(self):
        self.accumulators = dict()

        self.activity_counts = {
            "org": {},
            "sector": {},
            "country": {},
        }

        self.org_names = dict()

        self.this_month = datetime.utcnow().isoformat()[:7]

    #
    # Lookup functions
    #

    def get_org_name(self, org):
        """ Standardise organisation names
        For now, use the first name found for an identifier.
        Later, we can reference the registry.

        """
        ref = org.ref
        name = clean_string(str(org.name))

        if ref and ref in self.org_names:
            return self.org_names[ref]
        else:
            # FIXME - if the name is missing the first time, but there's an IATI identifier,
            # we'll have blanks initially; we need an initial table to prime it
            if name:
                self.org_names[ref] = name
                return name
            else:
                return "(Unspecified org)"

    @staticmethod
    def get_sector_group_name(code):
        """ Look up a group name for a 3- or 5-digit sector code.

        """
        sector_info = load_json("data/dac3-sector-map.json")
        code = code[:3]
        if code in sector_info:
            return sector_info.get(code)["dac-group"]
        else:
            return "(Unspecified sector)"

    @staticmethod
    def get_country_name(code):
        country_info = load_json("data/countries.json")
        for info in country_info["data"]:
            if info["iso2"] == code:
                return info["label"]["default"]
        return "(Unspecified country)"

    #
    # Business-logic functions
    #

    @staticmethod
    def make_country_splits(entity, default_country="XX"):
        """ Generate recipient-country splits by percentage for an activity or transaction
        FIXME - if there's no percentage for a country, default to 100% (could overcount)
        If there are no countries, assign 1.0 (100%) to the default provided.

        """
        splits = {}
        for country in entity.recipient_countries:
            code = country.code
            if code:
                splits[code.upper()] = float(country.percentage if country.percentage else 100.0) / 100.0
        return splits if splits else {default_country: 1.0}

    @staticmethod
    def make_sector_splits(entity, default_sector="99999"):
        """ Generate sector splits by percentage for an activity or transaction
        FIXME - if there's no percentage for a sector, default to 100% (could overcount)
        If there are no sectors, assign 1.0 (100%) to the default provided.
        """
        splits = {}
        sectors = entity.sectors

        # Prefer 3-digit codes to 5-digit
        if "2" in [sector.vocabulary for sector in sectors]:
            vocabulary_code = "2"
        else:
            vocabulary_code = "1"

        for sector in sectors:
            code = sector.code
            if sector.vocabulary == vocabulary_code and code:
                splits[code.upper()] = float(sector.percentage if sector.percentage else 100.0) / 100.0

        return splits if splits else {default_sector: 1.0}

    @staticmethod
    def has_c19_scope(scopes):
        """ Check if the COVID-19 GLIDE number or HRP code is present """
        for scope in scopes:
            if scope.type == "1" and scope.vocabulary == "1-2" and scope.code.upper() == "EP-2020-000012-001":
                return True
            elif scope.type == "2" and scope.vocabulary == "2-1" and scope.code.upper() == "HCOVD20":
                return True
        return False

    @staticmethod
    def has_c19_tag(tags):
        """ Check if the COVID-19 tag is present """
        for tag in tags:
            if tag.vocabulary == "99" and tag.code.upper() == "COVID-19":
                return True
        return False

    @staticmethod
    def has_c19_sector(sectors):
        """ Check if the DAC COVID-19 sector code is present """
        for sector in sectors:
            if sector.vocabulary == "1" and sector.code == "12264":
                return True
        return False

    @staticmethod
    def is_c19_narrative(narratives):
        """ Check a dict of different-language text for the string "COVID-19" (case-insensitive) """
        for lang, text in narratives.items():
            if "COVID-19" in text.upper():
                return True
        return False

    @classmethod
    def is_activity_strict(cls, activity):
        return True if (
                cls.has_c19_scope(activity.humanitarian_scopes) or
                cls.has_c19_tag(activity.tags) or
                cls.has_c19_sector(activity.sectors) or
                cls.is_c19_narrative(activity.title.narratives)
        ) else False

    @classmethod
    def is_transaction_strict(cls, transaction):
        return True if (
                cls.has_c19_sector(transaction.sectors) or
                (transaction.description and cls.is_c19_narrative(transaction.description.narratives))
        ) else False

    def process_activity(self, activity):
        #
        # Get the org name and C19 strictness (at activity level)
        #

        org = self.get_org_name(activity.reporting_org)
        activity_strict = self.is_activity_strict(activity)

        #
        # Figure out default country/sector percentage splits at the activity level
        #

        activity_country_splits = self.make_country_splits(activity)
        activity_sector_splits = self.make_sector_splits(activity)

        #
        # Figure out how to factor new money
        #

        # Total up the 4 kinds of transactions (with currency conversion to USD)
        transactions = Transactions(activity.transactions)
        incoming_funds = transactions.sum(["1"])
        outgoing_commitments = transactions.sum(["2"])
        spending = transactions.sum(["3", "4"])
        incoming_commitments = transactions.sum(["11"])

        # Figure out total incoming money (never less than zero)
        incoming = max(incoming_commitments, incoming_funds)
        if incoming < 0:
            incoming = 0

        # Factor to apply to outgoing commitments for net new money
        if incoming == 0:
            commitment_factor = 1.0
        elif outgoing_commitments > incoming:
            commitment_factor = (outgoing_commitments - incoming) / outgoing_commitments
        else:
            commitment_factor = 0.0

        # Factor to apply to outgoing spending for net new money
        if incoming == 0:
            spending_factor = 1.0
        elif spending > incoming:
            spending_factor = (spending - incoming) / spending
        else:
            spending_factor = 0.0

        #
        # Walk through the transactions one-by-one
        #

        for transaction in activity.transactions:

            #
            # Skip transactions with no values, or with out-of-range months
            #

            month = transaction.date[:7]
            if month < "2020-01" or month > self.this_month:
                continue

            if transaction.value is None:
                continue
            else:
                value = convert_to_usd(transaction.value, transaction.currency, transaction.date)

            #
            # Set the factors based on the type (commitments or spending)
            #

            if transaction.type == "2":
                # outgoing commitment
                type = "commitments"
                net_value = value * commitment_factor
            elif transaction.type in ["3", "4"]:
                # disbursement or expenditure (== spending)
                type = "spending"
                net_value = value * spending_factor
            else:
                # if it's anything else, skip it
                continue

            is_humanitarian = activity.humanitarian or transaction.humanitarian
            is_strict = activity_strict or self.is_transaction_strict(transaction)

            #
            # Values that go into the unique key
            #

            parts = {
                "month": month,
                "org": org,
                "country": None,
                "sector": None,
                "is_humanitarian": is_humanitarian,
                "is_strict": is_strict,
            }

            #
            # Make the splits for the transaction (default to activity splits)
            #

            country_splits = self.make_country_splits(transaction)
            sector_splits = self.make_sector_splits(transaction)

            #
            # Apply the country and sector percentage splits to the transaction
            # We may end up with multiple entries
            #

            for country, country_percentage in country_splits.items():
                for sector, sector_percentage in sector_splits.items():

                    net_money = int(round(net_value * country_percentage * sector_percentage))
                    total_money = int(round(value * country_percentage * sector_percentage))

                    # Fill in only if we end up with a non-zero value
                    if net_money or total_money:

                        # Fill in remaining parts for the key
                        parts["country"] = self.get_country_name(country)
                        parts["sector"] = self.get_sector_group_name(
                            sector)  # it doesn't matter if we get the same one more than once
                        key = pack_key(parts)

                        # Add a default entry if it doesn't exist yet
                        self.accumulators.setdefault(key, {
                            "net": {
                                "commitments": 0,
                                "spending": 0,
                            },
                            "total": {
                                "commitments": 0,
                                "spending": 0,
                            }
                        })

                        # Add the money to the self.accumulators
                        # FIXME: will double-count activities if the strict or humanitarian status of individual
                        # transactions differs in the same activity
                        self.accumulators[key]["net"][type] += net_money
                        self.accumulators[key]["total"][type] += total_money

                        # register the activity with the org, sector, and country separately
                        for key in ("org", "sector", "country",):
                            self.activity_counts[key].setdefault((parts[key], is_humanitarian, is_strict,), set()).add(
                                activity.identifier)
