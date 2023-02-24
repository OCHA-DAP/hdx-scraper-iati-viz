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

    def has_desired_text(self, narrativetext):
        # Check a dict of different-language text for the string "Food Security" or "Food Insecurity" (case-insensitive)
        for lang, text in narrativetext.narratives.items():
            if any(x in text.lower() for x in ("food security", "food insecurity")):
                return True
        return False

    def should_skip_transaction(self, dactivity, dtransaction, transaction_date):
        if not self.is_date_in_range(transaction_date):
            return True
        if (
            self.is_irrelevant_text(dactivity.title)
            and self.is_irrelevant_text(dactivity.description)
            and self.is_irrelevant_text(dtransaction.description)
            and self.is_irrelevant_sector(dtransaction.sectors)
        ):
            return True
        return False

    def get_activity_is_strict(self, dactivity):
        try:
            return (
                True
                if (
                    self.has_desired_text(dactivity.title)
                    or (
                        dactivity.description
                        and self.has_desired_text(dactivity.description)
                    )
                )
                else False
            )
        except AttributeError:
            self.errors_on_exit.add(
                f"Activity {dactivity.identifier} is_strict call failed!"
            )
            return False

    def get_transaction_is_strict(self, dactivity, activity_is_strict, dtransaction):
        try:
            is_strict = (
                True
                if (
                    dtransaction.description
                    and self.has_desired_text(dtransaction.description)
                )
                else False
            )
        except AttributeError:
            self.errors_on_exit.add(
                f"Activity {dactivity.identifier} transaction with usd value {dtransaction.usd_value} is_strict call failed!"
            )
            is_strict = False
        is_strict = is_strict or activity_is_strict
        return 1 if is_strict else 0

    def exclude_split_transaction(self, is_strict, sector, vocabulary_code):
        sectors_for_vocabulary = self.relevant_sectors.get(vocabulary_code)
        if sectors_for_vocabulary and sector not in sectors_for_vocabulary:
            return True
        return False
