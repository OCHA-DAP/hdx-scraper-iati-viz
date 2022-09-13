import logging

from hdx.location.currency import Currency, CurrencyError
from hdx.utilities.dateparse import parse_date

from .lookups import Lookups

logger = logging.getLogger(__name__)


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

    def include_date(self, datestr):
        if not datestr:
            return False
        date = parse_date(datestr)
        if self.start_date <= date <= self.today:
            return True
        return False

    def include_aid_type(self, aid_types):
        if not aid_types:
            return False
        for aid_type in aid_types:
            if aid_type.code not in self.excluded_aid_types:
                return True
        return False

    def include_country(self, countries):
        if not countries:
            return False
        for country in countries:
            if country.code in self.relevant_countries:
                return True
        return False

    def include_narrative(self, title_or_desc):
        if not title_or_desc:
            return False
        for lang, text in title_or_desc.narratives.items():
            text_lower = text.lower()
            for word in self.relevant_words:
                if word in text_lower:
                    return True
        return False

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

        if not do_checks or self.start_date is None:
            date_in_range = True
        else:
            date_in_range = self.include_date(dactivity.start_date_actual)
        if not do_checks or self.excluded_aid_types is None:
            included_aid_type = True
        else:
            included_aid_type = self.include_aid_type(dactivity.default_aid_types)
        if not do_checks or self.relevant_countries is None:
            country_in_list = True
        else:
            country_in_list = self.include_country(dactivity.recipient_countries)
        if not do_checks or self.relevant_words is None:
            text_in_narrative = True
        else:
            text_in_narrative = self.include_narrative(dactivity.title)
            if not text_in_narrative:
                text_in_narrative = self.include_narrative(dactivity.description)

        activityid = dactivity.identifier
        included_transactions = list()
        transaction_errors = list()
        for dtransaction in dactivity.transactions:
            if not included_aid_type:
                if not self.include_aid_type(dtransaction.aid_types):
                    continue
            if not country_in_list:
                if not self.include_country(dtransaction.recipient_countries):
                    continue
            if not text_in_narrative:
                if not self.include_narrative(dtransaction.description):
                    continue

            # We're not interested in transactions that have no value
            value = dtransaction.value
            if not value:
                continue
            # We're only interested in some transaction types
            transaction_type_info = Lookups.configuration["transaction_type_info"].get(
                dtransaction.type
            )
            if not transaction_type_info:
                continue
            currency = dtransaction.currency
            if currency is None:
                transaction_errors.append(
                    f"Excluding transaction with no currency (activity id {activityid}, value {value})!"
                )
                continue
            # Use value-date falling back on date
            date = dtransaction.value_date
            if not date:
                date = dtransaction.date
            if date:
                dtransaction.usddate = date
            else:
                transaction_errors.append(
                    f"Excluding transaction with no date (activity id {activityid}, value {value})!"
                )
                continue
            if not date_in_range:
                if not self.include_date(date):
                    continue
            try:
                usdvalue = Currency.get_historic_value_in_usd(
                    value, currency, parse_date(date)
                )
                dtransaction.usdvalue = usdvalue
                if usdvalue > Lookups.configuration[
                    "usd_error_threshold"
                ] and not Lookups.allow_activity(activityid):
                    Lookups.checks.errors_on_exit.add(
                        f"Transaction with value {value} in activity {activityid} exceeds threshold and is probably an error!"
                    )
            except (ValueError, CurrencyError):
                Lookups.checks.errors_on_exit.add(
                    f"Activity {activityid} transaction with value {value} USD conversion failed!"
                )
                continue
            included_transactions.append(dtransaction)

        if not date_in_range:
            return True, 0
        if not included_aid_type:
            return True, 0
        if not country_in_list:
            return True, 0
        if not text_in_narrative:
            return True, 0
        no_included_transactions = len(included_transactions)
        if no_included_transactions == 0:
            return True, 0
        for error in transaction_errors:
            Lookups.checks.errors_on_exit.add(error)
        removed = len(dactivity.transactions) - no_included_transactions
        dactivity.included_transactions = included_transactions
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
