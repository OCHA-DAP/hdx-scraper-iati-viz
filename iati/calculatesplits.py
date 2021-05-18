# -*- coding: utf-8 -*-

class CalculateSplits:
    @classmethod
    def setup(cls, configuration):
        splits_configuration = configuration['calculate_splits']
        cls.default_sector = splits_configuration['default_sector']
        cls.default_country = splits_configuration['default_country']

    @classmethod
    def make_country_splits(cls, entity, default_splits=None, default_country='XX'):
        """ Generate recipient-country splits by percentage for an activity or transaction
        FIXME - if there's no percentage for a country, default to 100% (could overcount)
        If there are no countries, assign 1.0 (100%) to the default provided.
        If default splits are provided (e.g. for an activity), use those.
        """
        splits = {}
        for country in entity.recipient_countries:
            code = country.code
            if code:
                splits[code.upper()] = float(country.percentage if country.percentage else 100.0) / 100.0

        if splits:
            # we have actual splits to return
            return splits
        elif default_splits is not None:
            # return the default splits
            return default_splits
        else:
            # default to 100% for unknown country
            return {default_country: 1.0}

    @classmethod
    def make_sector_splits(cls, entity, default_splits=None, default_sector='99999'):
        """ Generate sector splits by percentage for an activity or transaction
        FIXME - if there's no percentage for a sector, default to 100% (could overcount)
        If there are no sectors, assign 1.0 (100%) to the default provided.
        """
        splits = {}
        sectors = entity.sectors

        # Prefer 3-digit codes to 5-digit
        if '2' in [sector.vocabulary for sector in sectors]:
            vocabulary_code = '2'
        else:
            vocabulary_code = '1'

        for sector in sectors:
            code = sector.code
            if sector.vocabulary == vocabulary_code and code:
                splits[code.upper()] = float(sector.percentage if sector.percentage else 100.0) / 100.0

        if splits:
            # we have actual splits to return
            return splits
        elif default_splits is not None:
            # return the default splits
            return default_splits
        else:
            # default to 100% for unknown sector
            return {default_sector: 1.0}
