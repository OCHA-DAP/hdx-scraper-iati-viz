from hdx.utilities.dateparse import parse_date

from .lookups import Lookups


class BaseChecks:
    def __init__(self, errors_on_exit):
        self.errors_on_exit = errors_on_exit
        self.include_scope = True
        self.excluded_aid_types = None
        self.relevant_countries = None
        self.relevant_words = None

    def exclude_dactivity(
        self,
        dactivity,
    ):
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

        if self.include_scope:
            if self.has_desired_scope(dactivity):
                return False

        if Lookups.start_date is None:
            date_after_start_date = True
        else:
            date_after_start_date = False
        if self.excluded_aid_types is None:
            included_aid_type = True
        else:
            included_aid_type = False
        if self.relevant_countries is None:
            country_in_list = True
        else:
            country_in_list = False
        if self.relevant_words is None:
            text_in_narrative = True
        else:
            text_in_narrative = False

        def check_date(datestr):
            nonlocal date_after_start_date
            if date_after_start_date:
                return
            if not datestr:
                return
            date = parse_date(datestr)
            if date >= Lookups.start_date:
                date_after_start_date = True

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
        for dtransaction in dactivity.transactions:
            check_date(dtransaction.date)
            check_date(dtransaction.value_date)
            check_aid_types(dtransaction.aid_types)
            check_countries(dtransaction.recipient_countries)
            check_narratives(dtransaction.description)

        if not date_after_start_date:
            return True
        if not included_aid_type:
            return True
        if not country_in_list:
            return True
        if not text_in_narrative:
            return True
        return False

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
