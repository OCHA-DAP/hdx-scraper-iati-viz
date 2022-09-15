from .flatten import flatten


class SmallDActivity:
    __slots__ = [
        "identifier",
        "reporting_org",
        "humanitarian_scopes",
        "policy_markers",
        "tags",
        "sectors",
        "title",
        "humanitarian",
        "recipient_countries",
        "recipient_regions",
        "secondary_reporter",
        "hierarchy",
        "participating_orgs",
        "participating_orgs_by_role",
        "transactions",
    ]

    def __init__(self, dactivity):
        self.identifier = dactivity.identifier
        self.reporting_org = flatten(dactivity.reporting_org)
        self.humanitarian_scopes = flatten(dactivity.humanitarian_scopes)
        self.policy_markers = flatten(dactivity.policy_markers)
        self.tags = flatten(dactivity.tags)
        self.sectors = flatten(dactivity.sectors)
        self.title = flatten(dactivity.title)
        self.humanitarian = dactivity.humanitarian
        self.recipient_countries = flatten(dactivity.recipient_countries)
        self.recipient_regions = flatten(dactivity.recipient_regions)
        self.secondary_reporter = flatten(dactivity.secondary_reporter)
        self.hierarchy = dactivity.hierarchy
        self.participating_orgs = flatten(dactivity.participating_orgs)
        self.participating_orgs_by_role = flatten(dactivity.participating_orgs_by_role)
        self.transactions = dactivity.concrete_transactions
