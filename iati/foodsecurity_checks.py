from .base_checks import BaseChecks


class FoodSecurityChecks(BaseChecks):
    def __init__(self, today, start_date, errors_on_exit):
        super().__init__(today, start_date, errors_on_exit)
