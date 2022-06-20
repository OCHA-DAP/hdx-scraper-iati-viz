class EbolaChecks:
    @staticmethod
    def exclude_dactivity(dactivity):
        return False

    @staticmethod
    def get_scope_code(scopes):
        """Check if the Ebola code is present"""
        for scope in scopes:
            if scope.type == "2" and scope.vocabulary == "2-1":
                code = scope.code.upper() if scope.code else None
                if code == "OXEBOLA1415":
                    return code
        return None

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
        """Check a dict of different-language text for the string "EBOLA" (case-insensitive)"""
        for lang, text in narratives.items():
            if "ebola" in text.lower():
                return True
        return False
