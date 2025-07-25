from .base_checks import BaseChecks


class CovidChecks(BaseChecks):
    def __init__(self, today, start_date, errors_on_exit):
        super().__init__(today, start_date, errors_on_exit)

        self.excluded_aid_types = ("A01", "A02", "F01")

        # Check if the COVID-19 GLIDE number or HRP code is present
        def check_scope(scope):
            if (
                scope.type == "1"
                and scope.vocabulary == "1-2"
                and scope.code.upper() == "EP-2020-000012-001"
            ):
                return True
            elif (
                scope.type == "2"
                and scope.vocabulary == "2-1"
                and scope.code.upper() == "HCOVD20"
            ):
                return True
            return False

        self.add_scope_check(check_scope)

        # Check if the COVID-19 tag is present
        def check_tag(tag):
            if tag.vocabulary == "99" and tag.code.upper() == "COVID-19":
                return True
            return False

        self.add_tag_check(check_tag)

    def has_desired_sector(self, dactivity):
        """Check if the DAC COVID-19 sector code is present"""
        for sector in dactivity.sectors:
            if sector.vocabulary == "1" and sector.code == "12264":
                return True
        return False

    def has_desired_text(self, narrativetext):
        """Check a dict of different-language text for the string "COVID-19" (case-insensitive)"""
        for lang, text in narrativetext.narratives.items():
            if "covid-19" in text.lower():
                return True
        return False
