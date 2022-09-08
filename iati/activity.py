import logging

from .calculatesplits import CalculateSplits
from .lookups import Lookups
from .transaction import Transaction

logger = logging.getLogger(__name__)


class Activity:
    def __init__(self, dactivity):
        """
        Use the get_activity static method to construct
        """
        self.dactivity = dactivity
        self.identifier = dactivity.identifier
        # Get the reporting-org and C19 strictness at activity level
        self.org = Lookups.get_org_info(dactivity.reporting_org, reporting_org=True)
        self.strict = self.is_strict()
        self.humanitarian = dactivity.humanitarian
        # Figure out default country or region/sector percentage splits at the activity level
        self.countryregion_splits = CalculateSplits.make_country_or_region_splits(
            dactivity
        )
        self.sector_splits = CalculateSplits.make_sector_splits(dactivity)
        self.transactions = list()

    def add_transactions(self):
        skipped = 0
        for dtransaction in self.dactivity.transactions:
            transaction = Transaction.get_transaction(dtransaction, self.identifier)
            if not transaction:
                skipped += 1
                continue
            self.transactions.append(transaction)
        return skipped

    def is_strict(self):
        try:
            return (
                True
                if (
                    Lookups.checks.has_desired_scope(self.dactivity)
                    or Lookups.checks.has_desired_marker(self.dactivity)
                    or Lookups.checks.has_desired_tag(self.dactivity)
                    or Lookups.checks.has_desired_sector(self.dactivity)
                    or Lookups.checks.is_desired_narrative(
                        self.dactivity.title.narratives
                    )
                )
                else False
            )
        except AttributeError:
            logger.exception(f"Activity {self.identifier} is_strict call failed!")
            return False

    def sum_transactions_by_type(self):
        totals = dict()
        for transaction in self.transactions:
            key = f"{transaction.get_direction()} {transaction.get_classification()}"
            totals[key] = totals.get(key, 0) + transaction.value
        return totals

    def factor_new_money(self):
        #
        # Figure out how to factor new money
        #

        # Total up the 4 kinds of transactions (with currency conversion to USD)
        totals = self.sum_transactions_by_type()

        # Figure out total incoming money (never less than zero)
        incoming = max(
            totals.get("incoming commitments", 0), totals.get("incoming spending", 0)
        )
        if incoming < 0:
            incoming = 0

        # Factor to apply to outgoing commitments for net new money
        if incoming == 0:
            self.commitment_factor = 1.0
        else:
            outgoing_commitments = totals.get("outgoing commitments", 0)
            if outgoing_commitments > incoming:
                self.commitment_factor = (
                    outgoing_commitments - incoming
                ) / outgoing_commitments
            else:
                self.commitment_factor = 0.0

        # Factor to apply to outgoing spending for net new money
        if incoming == 0:
            self.spending_factor = 1.0
        else:
            spending = totals.get("outgoing spending", 0)
            if spending > incoming:
                self.spending_factor = (spending - incoming) / spending
            else:
                self.spending_factor = 0.0

    def add_to_flows(self, out_flows, transaction, funder, implementer):
        if transaction.get_classification() != "spending":
            return
        provider, receiver = transaction.get_provider_receiver()
        if funder and provider["name"] == Lookups.default_org_name:
            provider = funder
        if implementer and receiver["name"] == Lookups.default_org_name:
            receiver = implementer
        org_name = self.org["name"]
        if (
            org_name != Lookups.default_org_name
            and org_name != provider["name"]
            and org_name != receiver["name"]
        ):
            provider_name = provider["name"]
            if (
                not provider_name or provider_name == Lookups.default_org_name
            ) and provider["id"]:
                provider_name = provider["id"]
            receiver_name = receiver["name"]
            if (
                not receiver_name or receiver_name == Lookups.default_org_name
            ) and receiver["id"]:
                receiver_name = receiver["id"]
            key = (
                self.org["name"],
                provider_name,
                receiver_name,
                transaction.is_humanitarian,
                transaction.is_strict,
                transaction.get_direction(),
            )
            # ignore internal transactions or unknown reporting orgs
            cur_output = out_flows.get(key, dict())
            cur_output["value"] = cur_output.get("value", 0) + transaction.value
            if "row" not in cur_output:
                cur_output["row"] = [
                    self.org["id"],
                    self.org["name"],
                    self.org["type"],
                    provider["id"],
                    provider_name,
                    provider["type"],
                    receiver["id"],
                    receiver_name,
                    receiver["type"],
                    transaction.is_humanitarian,
                    transaction.is_strict,
                    transaction.get_direction(),
                ]
            out_flows[key] = cur_output

    def generate_split_transactions(self, out_transactions, transaction):
        # Make the splits for the transaction (default to activity splits)
        country_splits = transaction.make_country_or_region_splits(
            self.countryregion_splits
        )
        sector_splits = transaction.make_sector_splits(self.sector_splits)

        # Apply the country and sector percentage splits to the transaction
        # generate multiple split transactions
        for country, country_percentage in country_splits.items():
            for sector, sector_percentage in sector_splits.items():

                sector_name = Lookups.get_sector_group_name(sector)
                country_name = Lookups.get_country_region_name(country)

                #
                # Add to transactions
                #

                total_money = int(
                    round(transaction.value * country_percentage * sector_percentage)
                )
                net_money = int(
                    round(
                        transaction.net_value * country_percentage * sector_percentage
                    )
                )

                if total_money != 0:
                    # add to transactions
                    out_transactions.append(
                        [
                            transaction.date.strftime("%Y-%m"),
                            self.org["id"],
                            self.org["name"],
                            self.org["type"],
                            sector_name,
                            country_name,
                            transaction.is_humanitarian,
                            transaction.is_strict,
                            transaction.get_classification(),
                            self.identifier,
                            net_money,
                            total_money,
                        ]
                    )

    def get_funder_implementer(self):
        funder = None
        implementer = None
        participating_orgs_by_role = self.dactivity.participating_orgs_by_role
        for role in participating_orgs_by_role:
            if role not in ("1", "4"):
                continue
            participating_orgs = participating_orgs_by_role[role]
            if len(participating_orgs) != 1:
                continue
            org = Lookups.get_org_info(participating_orgs[0])
            if role == "1":
                funder = org
            else:
                implementer = org
        return funder, implementer

    def process(self, today, out_flows, out_transactions):
        self.factor_new_money()
        #
        # Walk through the activity's transactions one-by-one, and split by country/sector
        #
        funder, implementer = self.get_funder_implementer()
        skipped = 0
        for transaction in self.transactions:
            if not transaction.process(today, self):
                skipped += 1
                continue
            self.add_to_flows(out_flows, transaction, funder, implementer)
            if transaction.net_value is None:
                skipped += 1
                continue
            self.generate_split_transactions(out_transactions, transaction)
        return skipped
