from .base_checks import BaseChecks


class SouthSudanChecks(BaseChecks):
    def __init__(self, errors_on_exit):
        super().__init__(errors_on_exit)

        """Check if the Ebola code is present"""

        def check_scope(scope):
            if (
                scope.type == "2"
                and scope.vocabulary == "2-1"
                and scope.code.upper() in ("HSSD21", "HSSD22")
            ):
                return True
            return False

        self.add_scope_check(check_scope)
