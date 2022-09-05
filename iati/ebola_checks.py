from .base_checks import BaseChecks


class EbolaChecks(BaseChecks):
    def __init__(self, errors_on_exit):
        super().__init__(errors_on_exit)

        """Check if the Ebola code is present"""
        def check_scope(scope):
            if (
                scope.type == "2"
                and scope.vocabulary == "2-1"
                and scope.code.upper() == "OXEBOLA1415"
            ):
                return True
            return False

        self.add_scope_check(check_scope)

    def is_desired_narrative(self, narratives):
        """Check a dict of different-language text for the string "EBOLA" (case-insensitive)"""
        for lang, text in narratives.items():
            if "ebola" in text.lower():
                return True
        return False
