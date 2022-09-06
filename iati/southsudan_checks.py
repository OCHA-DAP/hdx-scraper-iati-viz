class SouthSudanChecks:
    @staticmethod
    def exclude_dactivity(dactivity):
        return False

    @staticmethod
    def has_desired_scope(dactivity):
        """Check if the South Sudan code is present"""
        for scope in dactivity.humanitarian_scopes:
            if (
                scope.type == "2"
                and scope.vocabulary == "2-1"
                and scope.code.upper() in ("HSSD21", "HSSD22")
            ):
                return True
        return False

    @staticmethod
    def has_desired_marker(dactivity):
        return False

    @staticmethod
    def has_desired_tag(dactivity):
        return False

    @staticmethod
    def has_desired_sector(dactivity):
        return False

    @staticmethod
    def is_desired_narrative(narratives):
        return False
