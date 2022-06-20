from iati.lookups import Lookups


class GlideChecks:
    @staticmethod
    def exclude_dactivity(dactivity):
        return False

    @staticmethod
    def get_scope_code(scopes):
        for scope in scopes:
            if scope.vocabulary == "1-2":
                code = scope.code.upper() if scope.code else None
                if code in Lookups.glide_codes:
                    return code
        return None

    @staticmethod
    def has_desired_marker(markers):
        return False

    @staticmethod
    def has_desired_tag(tags):
        return False

    @staticmethod
    def has_desired_sector(sectors):
        return False

    @staticmethod
    def is_desired_narrative(narratives):
        return False
