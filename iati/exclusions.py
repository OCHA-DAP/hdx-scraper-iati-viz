from dateutil.parser import ParserError
from hdx.location.currency import Currency, CurrencyError
from hdx.utilities.dateparse import parse_date

from .lookups import Lookups


class Exclusions:
    def __init__(self, today, start_date, errors_on_exit):
        self.today = today
        self.start_date = start_date
        self.errors_on_exit = errors_on_exit
        self.include_scope = True
        self.excluded_aid_types = None
        self.relevant_sectors = None
        self.relevant_countries = None
        self.relevant_words = None

    @staticmethod
    def specific_exclusions(dactivity):
        if dactivity.secondary_reporter:
            return True
        activity_identifier = dactivity.identifier
        # Filter out certain activities
        if Lookups.skip_activity(activity_identifier):
            return True
        reporting_org = dactivity.reporting_org
        if reporting_org is None:
            error = f"Excluding activity with no reporting org (activity id {activity_identifier})!"
            Lookups.checks.errors_on_exit.add(error)
            return True
        reporting_org_ref = reporting_org.ref
        # Filter out certain orgs
        if Lookups.skip_reporting_org(reporting_org_ref):
            return True
        # Filter out eg. GAVI and FCDO activities that have children (ie. filter out h=1)
        if Lookups.skip_reporting_org_children(reporting_org_ref, dactivity.hierarchy):
            return True
        return False

    def is_date_in_range(self, date):
        if date > self.today or (self.start_date and date < self.start_date):
            return False
        return True

    def is_excluded_aid_type(self, aid_types):
        if not self.excluded_aid_types:
            return False
        if not aid_types:
            return False
        for aid_type in aid_types:
            if aid_type.code not in self.excluded_aid_types:
                return False
        return True

    def is_irrelevant_sector(self, sectors):
        if not self.relevant_sectors:
            return False
        if not sectors:
            return False
        for sector in sectors:
            sectors_for_vocabulary = self.relevant_sectors.get(sector.vocabulary)
            if sectors_for_vocabulary:
                if sector.code in sectors_for_vocabulary:
                    return False
        return True

    def is_irrelevant_country(self, countries):
        if not self.relevant_countries:
            return False
        if not countries:
            return False
        for country in countries:
            if country.code in self.relevant_countries:
                return False
        return True

    def is_irrelevant_text(self, title_or_desc):
        if not self.relevant_words:
            return False
        if not title_or_desc:
            return False
        for lang, text in title_or_desc.narratives.items():
            text_lower = text.lower()
            for word in self.relevant_words:
                if word in text_lower:
                    return False
        return True

    @staticmethod
    def get_date_with_fallback(date1, date2):
        output_date = date1
        if output_date:
            try:
                output_date = parse_date(output_date)
            except ParserError:
                output_date = None
        if not output_date:
            output_date = date2
            if output_date:
                try:
                    output_date = parse_date(output_date)
                except ParserError:
                    output_date = None
            else:
                output_date = None
        return output_date

    # Prefilters either full activities and transactions that cannot be valued
    # Does not filter transactions other than those that cannot be valued as that must
    # happen after factoring new money
    def _exclude_activity(
        self,
        do_checks,
        dactivity,
    ):
        if not do_checks:
            date_in_range = True
        else:
            date_in_range = False
        if not do_checks or self.excluded_aid_types is None:
            included_aid_type = True
        else:
            included_aid_type = False
        if not do_checks or self.relevant_sectors is None:
            sector_in_list = True
        else:
            sector_in_list = False
        if not do_checks or self.relevant_countries is None:
            country_in_list = True
        else:
            country_in_list = False
        if not do_checks or self.relevant_words is None:
            text_in_narrative = True
        else:
            text_in_narrative = False

        def check_date(date):
            nonlocal date_in_range
            if date_in_range:
                return
            if not date:
                return
            if self.is_date_in_range(date):
                date_in_range = True

        def check_aid_types(aid_types):
            nonlocal included_aid_type
            if included_aid_type:
                return
            if not self.is_excluded_aid_type(aid_types):
                included_aid_type = True

        def check_sectors(sectors):
            nonlocal sector_in_list
            if sector_in_list:
                return
            if not self.is_irrelevant_sector(sectors):
                sector_in_list = True

        def check_countries(countries):
            nonlocal country_in_list
            if country_in_list:
                return
            if not self.is_irrelevant_country(countries):
                country_in_list = True

        def check_narratives(title_or_desc):
            nonlocal text_in_narrative
            if text_in_narrative:
                return
            if not self.is_irrelevant_text(title_or_desc):
                text_in_narrative = True

        no_transactions = len(dactivity.transactions)
        if no_transactions == 0:
            return True, None

        start_date = self.get_date_with_fallback(
            dactivity.start_date_actual, dactivity.start_date_planned
        )
        check_date(start_date)
        check_aid_types(dactivity.default_aid_types)
        check_sectors(dactivity.sectors)
        check_countries(dactivity.recipient_countries)
        check_narratives(dactivity.title)
        check_narratives(dactivity.description)

        activity_identifier = dactivity.identifier
        removed_transactions = list()
        remaining_transactions = 0
        transaction_errors = list()
        for i, dtransaction in enumerate(dactivity.transactions):
            check_aid_types(dtransaction.aid_types)
            check_sectors(dtransaction.sectors)
            check_countries(dtransaction.recipient_countries)
            check_narratives(dtransaction.description)
            # We're only interested in some transaction types
            transaction_type_info = Lookups.configuration["transaction_type_info"].get(
                dtransaction.type
            )
            if not transaction_type_info:
                removed_transactions.append(i)
                continue
            # We're not interested in transactions that have no value
            value = dtransaction.value
            if not value:
                removed_transactions.append(i)
                continue
            # We're not interested in transactions that have no currency
            currency = dtransaction.currency
            if currency is None:
                transaction_errors.append(
                    f"Excluding transaction with no currency (activity id {activity_identifier}, value {value})!"
                )
                removed_transactions.append(i)
                continue
            # We check the transaction date falling back on value date for the purposes
            # of filtering
            transaction_date = self.get_date_with_fallback(
                dtransaction.date, dtransaction.value_date
            )
            if transaction_date is None:
                transaction_errors.append(
                    f"Excluding transaction with invalid or no date (activity id {activity_identifier}, value {value})!"
                )
                removed_transactions.append(i)
                continue
            check_date(transaction_date)

            remaining_transactions += 1

        if (
            not date_in_range
            or not included_aid_type
            or not sector_in_list
            or not country_in_list
            or not text_in_narrative
            or remaining_transactions == 0
        ):
            return True, None

        for error in transaction_errors:
            Lookups.checks.errors_on_exit.add(error)
        return False, removed_transactions

    def exclude_transactions(self, dactivity):
        usd_error_threshold = Lookups.configuration["usd_error_threshold"]
        activity_identifier = dactivity.identifier
        filtered_transactions = list()
        transaction_errors = list()
        no_transactions = 0
        for dtransaction in dactivity.transactions:
            no_transactions += 1
            # For valuation, we use the value date falling back on transaction date
            valuation_date = self.get_date_with_fallback(
                dtransaction.value_date, dtransaction.date
            )
            value = dtransaction.value
            try:
                # Convert the transaction value to USD
                usd_value = Currency.get_historic_value_in_usd(
                    value,
                    dtransaction.currency,
                    valuation_date,
                )
            except (ValueError, CurrencyError):
                transaction_errors.append(
                    f"Excluding transaction that cannot be converted to USD (activity id {activity_identifier}, value {value})!"
                )
                continue
            if not usd_value:
                continue
            if usd_value > usd_error_threshold and not Lookups.allow_activity(
                activity_identifier
            ):
                transaction_errors.append(
                    f"Transaction with value {value} in activity {activity_identifier} exceeds threshold!"
                )
            dtransaction.value = usd_value
            filtered_transactions.append(dtransaction)

        dactivity.transactions = filtered_transactions
        no_valued_transactions = len(filtered_transactions)
        return no_valued_transactions, no_transactions - no_valued_transactions
