class CovidChecks:
    @staticmethod
    def has_desired_scope(scopes):
        """Check if the COVID-19 GLIDE number or HRP code is present"""
        for scope in scopes:
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

    @staticmethod
    def has_desired_tag(tags):
        """Check if the COVID-19 tag is present"""
        for tag in tags:
            if tag.vocabulary == "99" and tag.code.upper() == "COVID-19":
                return True
        return False

    @staticmethod
    def has_desired_sector(sectors):
        """Check if the DAC COVID-19 sector code is present"""
        for sector in sectors:
            if sector.vocabulary == "1" and sector.code == "12264":
                return True
        return False

    @staticmethod
    def is_desired_narrative(narratives):
        """Check a dict of different-language text for the string "COVID-19" (case-insensitive)"""
        for lang, text in narratives.items():
            if "COVID-19" in text.upper():
                return True
        return False
