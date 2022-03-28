class UkraineChecks:
    @staticmethod
    def has_desired_scope(scopes):
        """Check if the Ukraine code is present"""
        for scope in scopes:
            if (
                scope.type == "1"
                and scope.vocabulary == "1-2"
                and scope.code.upper() == "OT-2022-000157-UKR"
            ):
                return True
            elif (
                scope.type == "2"
                and scope.vocabulary == "2-1"
                and scope.code.upper() in ("FUKR22", "HUKR22", "RYKRN22")
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
