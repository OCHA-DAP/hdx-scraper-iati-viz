from hdx.location.currency import Currency, CurrencyError
from hdx.utilities.dateparse import parse_date

from .lookups import Lookups


class BaseChecks:
    def __init__(self, today, start_date, errors_on_exit):
        self.today = today
        self.start_date = start_date
        self.errors_on_exit = errors_on_exit
        self.include_scope = True
        self.excluded_aid_types = None
        self.relevant_countries = None
        self.relevant_words = None

    def specific_exclusions(self, dactivity):
        if dactivity.secondary_reporter:
            return True
        # Filter out certain activities
        if Lookups.skip_activity(dactivity.identifier):
            return True
        reporting_org_ref = dactivity.reporting_org.ref
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

    # Prefilters either full activities and transactions that cannot be valued
    # Does not filter transactions that are out of scope as that must happen after
    # factoring new money
    def exclude_activity(
        self,
        dactivity,
    ):
        if self.specific_exclusions(dactivity):
            return True, 0

        do_checks = True
        if self.include_scope:
            if self.has_desired_scope(dactivity):
                do_checks = False

        if not do_checks:
            date_in_range = True
        else:
            date_in_range = False
        if not do_checks or self.excluded_aid_types is None:
            included_aid_type = True
        else:
            included_aid_type = False
        if not do_checks or self.relevant_countries is None:
            country_in_list = True
        else:
            country_in_list = False
        if not do_checks or self.relevant_words is None:
            text_in_narrative = True
        else:
            text_in_narrative = False

        def check_date(datestr):
            nonlocal date_in_range
            if date_in_range:
                return
            if not datestr:
                return
            if self.is_date_in_range(parse_date(datestr)):
                date_in_range = True

        def check_aid_types(aid_types):
            nonlocal included_aid_type
            if included_aid_type:
                return
            if not aid_types:
                return
            for aid_type in aid_types:
                if aid_type.code not in self.excluded_aid_types:
                    included_aid_type = True
                    return

        def check_countries(countries):
            nonlocal country_in_list
            if country_in_list:
                return
            if not countries:
                return
            for country in countries:
                if country.code in self.relevant_countries:
                    country_in_list = True
                    return

        def check_narratives(title_or_desc):
            nonlocal text_in_narrative
            if text_in_narrative:
                return
            if not title_or_desc:
                return
            for lang, text in title_or_desc.narratives.items():
                text_lower = text.lower()
                for word in self.relevant_words:
                    if word in text_lower:
                        text_in_narrative = True
                        return

        check_date(dactivity.start_date_actual)
        check_aid_types(dactivity.default_aid_types)
        check_countries(dactivity.recipient_countries)
        check_narratives(dactivity.title)
        check_narratives(dactivity.description)

        activity_identifier = dactivity.identifier
        concrete_transactions = list()
        transaction_errors = list()
        usd_error_threshold = Lookups.configuration["usd_error_threshold"]
        for dtransaction in dactivity.transactions:
            check_aid_types(dtransaction.aid_types)
            check_countries(dtransaction.recipient_countries)
            check_narratives(dtransaction.description)
            # We're only interested in some transaction types
            transaction_type_info = Lookups.configuration["transaction_type_info"].get(
                dtransaction.type
            )
            if not transaction_type_info:
                continue
            # We're not interested in transactions that have no value
            value = dtransaction.value
            if not value:
                continue
            # We're not interested in transactions that have no currency
            currency = dtransaction.currency
            if currency is None:
                transaction_errors.append(
                    f"Excluding transaction with no currency (activity id {activity_identifier}, value {value})!"
                )
                continue
            # We check the transaction date falling back on value date for the purposes
            # of filtering
            transaction_date = dtransaction.date
            valuation_date = dtransaction.value_date
            if not transaction_date:
                transaction_date = valuation_date
                if not transaction_date:
                    transaction_errors.append(
                        f"Excluding transaction with no date (activity id {activity_identifier}, value {value})!"
                    )
                    continue
            check_date(transaction_date)

            # For valuation, we use the value date falling back on transaction date
            if not valuation_date:
                valuation_date = transaction_date
            try:
                # Convert the transaction value to USD
                usd_value = Currency.get_historic_value_in_usd(
                    value,
                    currency,
                    parse_date(valuation_date),
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
            dtransaction.transaction_date = transaction_date
            dtransaction.usd_value = usd_value
            concrete_transactions.append(dtransaction)

        if not date_in_range:
            return True, 0
        if not included_aid_type:
            return True, 0
        if not country_in_list:
            return True, 0
        if not text_in_narrative:
            return True, 0
        no_transactions = len(concrete_transactions)
        if no_transactions == 0:
            return True, 0
        for error in transaction_errors:
            Lookups.checks.errors_on_exit.add(error)
        removed = len(dactivity.transactions) - no_transactions
        dactivity.concrete_transactions = concrete_transactions
        return False, removed

    def has_desired_scope(self, dactivity):
        return False

    def add_scope_check(self, fn):
        def check_fn(dactivity):
            for scope in dactivity.humanitarian_scopes:
                if scope.code is None:
                    self.errors_on_exit.add(
                        f"Activity {dactivity.identifier} has no humanitarian scope code!"
                    )
                    continue
                if fn(scope):
                    return True
            return False

        self.has_desired_scope = check_fn

    def has_desired_marker(self, dactivity):
        return False

    def has_desired_tag(self, dactivity):
        return False

    def add_tag_check(self, fn):
        def check_fn(dactivity):
            for tag in dactivity.tags:
                if tag.code is None:
                    self.errors_on_exit.add(
                        f"Activity {dactivity.identifier} has no tag code!"
                    )
                    continue
                if fn(tag):
                    return True
            return False

        self.has_desired_tag = check_fn

    def has_desired_sector(self, dactivity):
        return False

    def is_desired_narrative(self, narratives):
        return False
