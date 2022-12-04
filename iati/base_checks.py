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

    def is_desired_narrative(self, narratives):
        return False

    def should_skip_transaction(self, dactivity, dtransaction, transaction_date):
        if not self.is_date_in_range(transaction_date):
            return True
        if self.is_excluded_aid_type(dtransaction.aid_types):
            return True
        return False
