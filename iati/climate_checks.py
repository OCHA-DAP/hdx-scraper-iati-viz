from .base_checks import BaseChecks


class ClimateChecks(BaseChecks):
    def has_desired_marker(self, dactivity):
        for marker in dactivity.policy_markers:
            if marker.vocabulary != "1":
                continue
            if marker.code not in ("6", "7"):
                continue
            if marker.significance in ("1", "2", "3", "4"):
                return True
        return False

    def has_desired_text(self, narrativetext):
        """Check a dict of different-language text for the string "climate finance" (case-insensitive)"""
        for lang, text in narrativetext.narratives.items():
            if "climate finance" in text.lower():
                return True
        return False
