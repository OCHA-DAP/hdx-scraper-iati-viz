from .base_checks import BaseChecks


class CovidChecks(BaseChecks):
    def has_desired_scope(self, dactivity):
        """Check if the COVID-19 GLIDE number or HRP code is present"""
        for scope in dactivity.humanitarian_scopes:
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

    def has_desired_tag(self, dactivity):
        """Check if the COVID-19 tag is present"""
        for tag in dactivity.tags:
            if tag.vocabulary == "99" and tag.code.upper() == "COVID-19":
                return True
        return False

    def has_desired_sector(self, dactivity):
        """Check if the DAC COVID-19 sector code is present"""
        for sector in dactivity.sectors:
            if sector.vocabulary == "1" and sector.code == "12264":
                return True
        return False

    def is_desired_narrative(self, narratives):
        """Check a dict of different-language text for the string "COVID-19" (case-insensitive)"""
        for lang, text in narratives.items():
            if "covid-19" in text.lower():
                return True
        return False
