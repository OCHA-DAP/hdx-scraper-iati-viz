from hdx.utilities.dateparse import parse_date


class UkraineChecks:
    @classmethod
    def exclude_dactivity(cls, dactivity):
        if cls.has_desired_scope(dactivity.humanitarian_scopes):
            return False
        #        if not dactivity.humanitarian:
        #            return True
        #        if dactivity.activity_status != "2":
        #            return True
        conflict_start_date = parse_date("2022-02-24")
        excluded_aid_types = ("A01",)
        relevant_countries = ("UA", "PL", "HU", "SK", "RO", "MD", "BY", "RU")
        start_date_in_conflict = False
        included_aid_type = False
        country_in_list = False
        text_in_narrative = False

        def check_date(date):
            nonlocal conflict_start_date, start_date_in_conflict
            if start_date_in_conflict:
                return
            if not date:
                return
            start_date = parse_date(date)
            if start_date >= conflict_start_date:
                start_date_in_conflict = True

        def check_aid_types(aid_types):
            nonlocal excluded_aid_types, included_aid_type
            if included_aid_type:
                return
            if not aid_types:
                return
            for aid_type in aid_types:
                if aid_type.code not in excluded_aid_types:
                    included_aid_type = True
                    return

        def check_countries(countries):
            nonlocal relevant_countries, country_in_list
            if country_in_list:
                return
            if not countries:
                return
            for country in countries:
                if country.code in relevant_countries:
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
                if "ukraine" in text_lower or "ukrainian" in text_lower:
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

        #        if not country_in_list:
        #            return True
        if not included_aid_type:
            return True
        if not start_date_in_conflict:
            return True
        if not text_in_narrative:
            return True
        return False

    @staticmethod
    def has_desired_scope(scopes):
        """Check if the Ukraine code is present"""
        for scope in scopes:
            if (
                scope.type == "1"
                and scope.vocabulary == "1-2"
                and scope.code.upper() == "OT-2022-000157-UKR"
            ):
                return True
            elif scope.type == "2":
                if scope.vocabulary == "2-1" and scope.code.upper() in (
                    "FUKR22",
                    "RUKRN22",
                    "HUKR22",
                ):
                    return True
                if (
                    scope.vocabulary == "99"
                    and scope.code.upper() == "UKRAINE-REGIONAL-RRP-2022"
                ):
                    return True
        return False

    @staticmethod
    def has_desired_marker(markers):
        return False

    @staticmethod
    def has_desired_tag(tags):
        return False

    @staticmethod
    def has_desired_sector(sectors):
        return False

    @staticmethod
    def is_desired_narrative(narratives):
        return False
