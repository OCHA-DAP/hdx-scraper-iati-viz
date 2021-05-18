# -*- coding: utf-8 -*-
from hdx.location.country import Country
from hdx.utilities.loader import load_json

from iati.utils import clean_string


class Lookups:
    org_names = dict()
    default_org = None
    sector_info = None
    default_sector = None
    default_country = None

    @classmethod
    def setup(cls, configuration):
        lookups_configuration = configuration['lookups']
        org_data = load_json(lookups_configuration['org_data'])
        """ Map from IATI identifiers to organisation names """
        # Prime with org identifiers from code4iati
        for entry in org_data['data']:
            code = clean_string(entry['code']).lower()
            cls.org_names[code] = clean_string(entry['name'])
        cls.sector_info = load_json(lookups_configuration['sector_data'])
        cls.default_org = lookups_configuration['default_org']
        cls.default_sector = lookups_configuration['default_sector']
        cls.default_country = lookups_configuration['default_country']

    @classmethod
    def get_org_name(cls, org):
        """ Standardise organisation names
        For now, use the first name found for an identifier.
        Later, we can reference the registry.
        """
        name = None if org is None or org.name is None else clean_string(str(org.name))
        ref = None if org is None or org.ref is None else clean_string(str(org.ref)).lower()

        # We have a ref and an existing match
        if ref and ref in cls.org_names:
            # existing match
            return cls.org_names[ref]

        # No existing match, but we have a name
        if name:
            if ref is not None:
                # if there's a ref, save it for future matching
                cls.org_names[ref] = name
            return name

        # We can't figure out anything
        return cls.default_org

    @classmethod
    def get_sector_group_name(cls, code):
        """ Look up a group name for a 3- or 5-digit sector code.
        """
        code = code[:3]
        if code in cls.sector_info:
            return cls.sector_info.get(code)['dac-group']
        else:
            return cls.default_sector

    @classmethod
    def get_country_name(cls, code):
        countryname = Country.get_country_name_from_iso2(code)
        if countryname:
            return countryname
        return cls.default_country
