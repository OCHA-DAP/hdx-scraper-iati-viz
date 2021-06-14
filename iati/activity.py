# -*- coding: utf-8 -*-
from iati.calculatesplits import CalculateSplits
from iati.covidchecks import has_c19_scope, has_c19_tag, has_c19_sector, is_c19_narrative
from iati.lookups import Lookups
from iati.transaction import Transaction


class Activity:
    def __init__(self, dactivity):
        """
        Use the get_activity static method to construct
        """
        self.dactivity = dactivity
        self.identifier = dactivity.identifier
        # Get the reporting-org and C19 strictness at activity level
        self.org = Lookups.get_org_id_name(dactivity.reporting_org)
        self.org_type = str(dactivity.reporting_org.type)
        self.strict = self.is_strict()
        self.humanitarian = dactivity.humanitarian
        # Figure out default country/sector percentage splits at the activity level
        self.country_splits = CalculateSplits.make_country_splits(dactivity)
        self.sector_splits = CalculateSplits.make_sector_splits(dactivity)
        self.transactions = list()

    def add_transactions(self, configuration):
        skipped = 0
        for dtransaction in self.dactivity.transactions:
            transaction = Transaction.get_transaction(configuration, dtransaction)
            if not transaction:
                skipped += 1
                continue
            self.transactions.append(transaction)
        return skipped

    @staticmethod
    def get_activity(configuration, dactivity):
        """
        We exclude activities from secondary reporters and certain sorts
        of organisations where the data is very poor quality. We also
        exclude hierarchy=1 activities for UNDP (XM-DAC-41114) and FCDO (GB-GOV-1).
        """
        # Skip activities from a secondary reporter
        if dactivity.secondary_reporter:
            return None, len(dactivity.transactions)
        reporting_org_ref = dactivity.reporting_org.ref
        # Filter out certain orgs
        if Lookups.is_filter_reporting_orgs(reporting_org_ref):
            return None, len(dactivity.transactions)
        # Filter out eg. UNDP and DFID activities that have children (i.e. filter out h=1)
        if Lookups.is_filter_reporting_orgs_children(reporting_org_ref):
            if '2' in dactivity.related_activities_by_type:
                return None, len(dactivity.transactions)
        activity = Activity(dactivity)
        skipped = activity.add_transactions(configuration)
        return activity, skipped

    def is_strict(self):
        return True if (has_c19_scope(self.dactivity.humanitarian_scopes) or has_c19_tag(self.dactivity.tags) or
                        has_c19_sector(self.dactivity.sectors) or is_c19_narrative(self.dactivity.title.narratives)) \
            else False

    def sum_transactions_by_type(self):
        totals = dict()
        for transaction in self.transactions:
            key = f'{transaction.direction} {transaction.classification}'
            totals[key] = totals.get(key, 0) + transaction.value
        return totals

    def factor_new_money(self):
        #
        # Figure out how to factor new money
        #

        # Total up the 4 kinds of transactions (with currency conversion to USD)
        totals = self.sum_transactions_by_type()

        # Figure out total incoming money (never less than zero)
        incoming = max(totals.get('incoming commitments', 0), totals.get('incoming spending', 0))
        if incoming < 0:
            incoming = 0

        # Factor to apply to outgoing commitments for net new money
        if incoming == 0:
            self.commitment_factor = 1.0
        else:
            outgoing_commitments = totals.get('outgoing commitments', 0)
            if outgoing_commitments > incoming:
                self.commitment_factor = (outgoing_commitments - incoming) / outgoing_commitments
            else:
                self.commitment_factor = 0.0

        # Factor to apply to outgoing spending for net new money
        if incoming == 0:
            self.spending_factor = 1.0
        else:
            spending = totals.get('outgoing spending', 0)
            if spending > incoming:
               self.spending_factor = (spending - incoming) / spending
            else:
                self.spending_factor = 0.0

    def add_to_flows(self, out_flows, transaction, funder, implementer):
        provider, receiver = transaction.get_provider_receiver()
        if funder and provider['name'] == Lookups.default_org_name:
            provider = funder
        if implementer and receiver['name'] == Lookups.default_org_name:
            receiver = implementer
        org_name = self.org['name']
        if org_name != Lookups.default_org_name and org_name != provider['name'] and org_name != receiver['name']:
            key = (self.org['id'], self.org['name'], self.org_type, provider['id'], provider['name'],
                   receiver['id'], receiver['name'], transaction.is_humanitarian, transaction.is_strict,
                   transaction.classification, transaction.direction)
            # ignore internal transactions or unknown reporting orgs
            out_flows[key] = out_flows.get(key, 0) + transaction.value

    def generate_split_transactions(self, out_transactions, transaction):
        # Make the splits for the transaction (default to activity splits)
        country_splits = transaction.make_country_splits(self.country_splits)
        sector_splits = transaction.make_sector_splits(self.sector_splits)

        # Apply the country and sector percentage splits to the transaction
        # generate multiple split transactions
        for country, country_percentage in country_splits.items():
            for sector, sector_percentage in sector_splits.items():

                sector_name = Lookups.get_sector_group_name(sector)
                country_name = Lookups.get_country_name(country)

                #
                # Add to transactions
                #

                total_money = int(round(transaction.value * country_percentage * sector_percentage))
                net_money = int(round(transaction.net_value * country_percentage * sector_percentage))

                if total_money != 0:
                    # add to transactions
                    out_transactions.append([transaction.month, self.org['id'], self.org['name'], self.org_type,
                                             sector_name, country_name, transaction.is_humanitarian,
                                             transaction.is_strict, transaction.classification, self.identifier,
                                             net_money, total_money])

    def get_funder_implementer(self):
        funder = None
        implementer = None
        participating_orgs_by_role = self.dactivity.participating_orgs_by_role
        for role in participating_orgs_by_role:
            if role not in ('1', '4'):
                continue
            participating_orgs = participating_orgs_by_role[role]
            if len(participating_orgs) != 1:
                continue
            org = Lookups.get_org_id_name(participating_orgs[0])
            if role == '1':
                funder = org
            else:
                implementer = org
        return funder, implementer

    def process(self, this_month, out_flows, out_transactions):
        self.factor_new_money()
        #
        # Walk through the activity's transactions one-by-one, and split by country/sector
        #
        funder, implementer = self.get_funder_implementer()
        skipped = 0
        for transaction in self.transactions:
            if not transaction.process(this_month, self):
                skipped += 1
                continue
            self.add_to_flows(out_flows, transaction, funder, implementer)
            if transaction.net_value is None:
                skipped += 1
                continue
            self.generate_split_transactions(out_transactions, transaction)
        return skipped