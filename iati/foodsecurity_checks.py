from .base_checks import BaseChecks


class FoodSecurityChecks(BaseChecks):
    def __init__(self, today, start_date, errors_on_exit):
        super().__init__(today, start_date, errors_on_exit)

    def is_desired_narrative(self, narratives):
        # Check a dict of different-language text for the string "Food Security" or "Food Insecurity" (case-insensitive)
        for lang, text in narratives.items():
            if any(x in text.lower() for x in ("food security", "food insecurity")):
                return True
        return False
