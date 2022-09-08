from .base_checks import BaseChecks


class UkraineChecks(BaseChecks):
    def __init__(self, errors_on_exit):
        super().__init__(errors_on_exit)
        self.include_scope = True
        self.excluded_aid_types = ("A01", "A02", "F01")
        self.relevant_words = ("ukraine", "ukrainian")

        # Check if the Ukraine code is present
        def check_scope(scope):
            if (
                scope.type == "1"
                and scope.vocabulary == "1-2"
                and scope.code.upper() == "OT-2022-000157-UKR"
            ):
                return True
            elif scope.type == "2":
                if scope.vocabulary == "2-1" and scope.code.upper() in (
                    "FUKR22",
                    "RUKRN22",
                    "HUKR22",
                ):
                    return True
                if (
                    scope.vocabulary == "99"
                    and scope.code.upper() == "UKRAINE-REGIONAL-RRP-2022"
                ):
                    return True
            return False

        self.add_scope_check(check_scope)
