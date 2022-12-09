from .exclusions import Exclusions


class BaseChecks(Exclusions):
    # Prefilters either full activities and transactions that cannot be valued
    # Does not filter transactions oteh than those that cannot be valued as that must
    # happen after factoring new money
    def exclude_activity(
        self,
        dactivity,
    ):
        if self.specific_exclusions(dactivity):
            return True, 0

        do_checks = True
        if self.include_scope:
            if self.has_desired_scope(dactivity):
                do_checks = False
        return self._exclude_activity(do_checks, dactivity)

    def has_desired_scope(self, dactivity):
        return False

    def add_scope_check(self, fn):
        def check_fn(dactivity):
            for scope in dactivity.humanitarian_scopes:
                if scope.code is None:
                    self.errors_on_exit.add(
                        f"Activity {dactivity.identifier} has no humanitarian scope code!"
                    )
                    continue
                if fn(scope):
                    return True
            return False

        self.has_desired_scope = check_fn

    def has_desired_marker(self, dactivity):
        return False

    def has_desired_tag(self, dactivity):
        return False

    def add_tag_check(self, fn):
        def check_fn(dactivity):
            for tag in dactivity.tags:
                if tag.code is None:
                    self.errors_on_exit.add(
                        f"Activity {dactivity.identifier} has no tag code!"
                    )
                    continue
                if fn(tag):
                    return True
            return False

        self.has_desired_tag = check_fn

    def has_desired_sector(self, dactivity):
        return False

    def has_desired_text(self, narrativetext):
        return False

    def should_skip_transaction(self, dactivity, dtransaction, transaction_date):
        if not self.is_date_in_range(transaction_date):
            return True
        if self.is_excluded_aid_type(dtransaction.aid_types):
            return True
        return False

    def get_activity_is_strict(self, dactivity):
        try:
            return (
                True
                if (
                    self.has_desired_scope(dactivity)
                    or self.has_desired_marker(dactivity)
                    or self.has_desired_tag(dactivity)
                    or self.has_desired_sector(dactivity)
                    or self.has_desired_text(dactivity.title)
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
                    self.has_desired_sector(dtransaction)
                    or (
                        dtransaction.description
                        and self.has_desired_text(dtransaction.description)
                    )
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

    def exclude_split_transaction(self, activity_is_strict, sector, vocabulary_code):
        return False
