class BaseChecks:
    def __init__(self, errors_on_exit):
        self.errors_on_exit = errors_on_exit

    def exclude_dactivity(self, dactivity):
        return False

    def has_desired_scope(self, dactivity):
        return False

    def add_scope_check(self, fn):
        def check_fn(dactivity):
            for scope in dactivity.humanitarian_scopes:
                if scope.code is None:
                    self.errors_on_exit.add(
                        f"Activity {dactivity.identifier} has no humanitarian scope code!")
                    continue
                if fn(scope):
                    return True
            return False

        self.has_desired_scope = check_fn

    def has_desired_marker(self, dactivity):
        return False

    def add_marker_check(self, fn):
        def check_fn(dactivity):
            for marker in dactivity.policy_markers:
                if marker.code is None:
                    self.errors_on_exit.add(
                        f"Activity {dactivity.identifier} has no policy marker code!")
                    continue
                if fn(marker):
                    return True
            return False

        self.has_desired_marker = check_fn

    def has_desired_tag(self, dactivity):
        return False

    def add_tag_check(self, fn):
        def check_fn(dactivity):
            for tag in dactivity.tags:
                if tag.code is None:
                    self.errors_on_exit.add(
                        f"Activity {dactivity.identifier} has no tag code!")
                    continue
                if fn(tag):
                    return True
            return False

        self.has_desired_tag = check_fn

    def has_desired_sector(self, dactivity):
        return False

    def add_sector_check(self, fn):
        def check_fn(dactivity):
            for sector in dactivity.sectors:
                if sector.code is None:
                    self.errors_on_exit.add(
                        f"Activity {dactivity.identifier} has no sector code!")
                    continue
                if fn(sector):
                    return True
            return False

        self.has_desired_sector = check_fn

    def is_desired_narrative(self, dactivity):
        return False

