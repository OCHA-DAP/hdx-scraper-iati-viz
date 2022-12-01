from .base_checks import BaseChecks


class FoodSecurityChecks(BaseChecks):
    def __init__(self, today, start_date, errors_on_exit):
        super().__init__(today, start_date, errors_on_exit)
        self.relevant_sectors = {
            "1": (
                "11250",
                "12240",
                "31110",
                "31120",
                "31130",
                "31140",
                "31150",
                "31161",
                "31162",
                "31163",
                "31164",
                "31165",
                "31166",
                "31181",
                "31182",
                "31191",
                "31192",
                "31193",
                "31194",
                "31195",
                "31210",
                "31220",
                "31261",
                "31281",
                "31282",
                "31291",
                "31310",
                "31320",
                "31381",
                "31382",
                "31391",
                "32161",
                "32162",
                "43040",
                "43071",
                "43072",
                "43073",
                "52010",
            ),
            "2": ("311", "312", "313"),
        }
        self.relevant_words = ("food security", "food insecurity")

    def is_desired_narrative(self, narratives):
        # Check a dict of different-language text for the string "Food Security" or "Food Insecurity" (case-insensitive)
        for lang, text in narratives.items():
            if any(x in text.lower() for x in ("food security", "food insecurity")):
                return True
        return False
