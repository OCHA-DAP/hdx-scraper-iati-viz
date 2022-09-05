from iati.lookups import Lookups


class CalculateSplits:
    default_sector = None
    default_country_region = None

    @classmethod
    def setup(cls):
        configuration = Lookups.configuration["calculate_splits"]
        cls.default_sector = configuration["default_sector"]
        cls.default_country_region = configuration["default_country_region"]

    @classmethod
    def make_country_or_region_splits(cls, entity, default_splits=None):
        """Generate recipient-country or recipient-region splits by percentage for an activity or transaction
        FIXME - if there's no percentage for a country/region, default to 100% (could overcount)
        If there are no countries or regions, assign 1.0 (100%) to the default provided.
        If default splits are provided (e.g. for an activity), use those.
        """
        splits = {}
        for country in entity.recipient_countries:
            code = country.code
            if code:
                splits[code.upper()] = (
                    float(country.percentage if country.percentage else 100.0) / 100.0
                )
        for region in entity.recipient_regions:
            if region.vocabulary != "1":
                continue
            code = region.code
            if code:
                splits[code.upper()] = (
                    float(region.percentage if region.percentage else 100.0) / 100.0
                )

        if splits:
            # we have actual splits to return
            return splits
        elif default_splits is not None:
            # return the default splits
            return default_splits
        else:
            # default to 100% for unknown country
            return {cls.default_country_region: 1.0}

    @classmethod
    def make_sector_splits(cls, entity, default_splits=None, default_sector=None):
        """Generate sector splits by percentage for an activity or transaction
        FIXME - if there's no percentage for a sector, default to 100% (could overcount)
        If there are no sectors, assign 1.0 (100%) to the default provided.
        """
        splits = {}
        sectors = entity.sectors

        # Prefer 3-digit codes to 5-digit
        if "2" in [sector.vocabulary for sector in sectors]:
            vocabulary_code = "2"
        else:
            vocabulary_code = "1"

        for sector in sectors:
            code = sector.code
            if sector.vocabulary == vocabulary_code and code:
                splits[code.upper()] = (
                    float(sector.percentage if sector.percentage else 100.0) / 100.0
                )

        if splits:
            # we have actual splits to return
            return splits
        elif default_splits is not None:
            # return the default splits
            return default_splits
        else:
            # default to 100% for unknown sector
            if default_sector is None:
                return {cls.default_sector: 1.0}
            return {default_sector: 1.0}
