class ClimateChecks:
    @staticmethod
    def has_desired_scope(dactivity):
        return False

    @staticmethod
    def has_desired_marker(dactivity):
        for marker in dactivity.policy_markers:
            if marker.vocabulary != "1":
                continue
            if marker.code not in ("6", "7"):
                continue
            if marker.significance in ("1", "2", "3", "4"):
                return True
        return False

    @staticmethod
    def has_desired_tag(dactivity):
        return False

    @staticmethod
    def has_desired_sector(dactivity):
        return False

    @staticmethod
    def is_desired_narrative(narratives):
        """Check a dict of different-language text for the string "climate finance" (case-insensitive)"""
        for lang, text in narratives.items():
            if "climate finance" in text.lower():
                return True
        return False
