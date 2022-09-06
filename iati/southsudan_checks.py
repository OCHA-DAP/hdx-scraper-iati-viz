from .base_checks import BaseChecks


class SouthSudanChecks(BaseChecks):
    def has_desired_scope(self, dactivity):
        """Check if the South Sudan code is present"""
        for scope in dactivity.humanitarian_scopes:
            if (
                scope.type == "2"
                and scope.vocabulary == "2-1"
                and scope.code.upper() in ("HSSD21", "HSSD22")
            ):
                return True
        return False
