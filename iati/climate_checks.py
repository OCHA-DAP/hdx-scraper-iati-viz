from .base_checks import BaseChecks


class ClimateChecks(BaseChecks):
    def __init__(self, errors_on_exit):
        super().__init__(errors_on_exit)

        def check_marker(marker):
            if marker.vocabulary != "1":
                return False
            if marker.code not in ("6", "7"):
                return False
            if marker.significance in ("1", "2", "3", "4"):
                return True
            return False

        self.add_marker_check(check_marker)

    def is_desired_narrative(self, narratives):
        """Check a dict of different-language text for the string "climate finance" (case-insensitive)"""
        for lang, text in narratives.items():
            if "climate finance" in text.lower():
                return True
        return False
