from .base_checks import BaseChecks


class EbolaChecks(BaseChecks):
    def has_desired_scope(self, dactivity):
        """Check if the Ebola code is present"""
        for scope in dactivity.humanitarian_scopes:
            if (
                scope.type == "2"
                and scope.vocabulary == "2-1"
                and scope.code.upper() == "OXEBOLA1415"
            ):
                return True
        return False

    def is_desired_narrative(self, narratives):
        """Check a dict of different-language text for the string "EBOLA" (case-insensitive)"""
        for lang, text in narratives.items():
            if "ebola" in text.lower():
                return True
        return False
