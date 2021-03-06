class SouthSudanChecks:
    @staticmethod
    def exclude_dactivity(dactivity):
        return False

    @staticmethod
    def has_desired_scope(scopes):
        """Check if the South Sudan code is present"""
        for scope in scopes:
            if (
                scope.type == "2"
                and scope.vocabulary == "2-1"
                and scope.code.upper() in ("HSSD21", "HSSD22")
            ):
                return True
        return False

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
        return False
