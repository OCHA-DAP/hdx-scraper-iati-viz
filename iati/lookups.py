# -*- coding: utf-8 -*-
import logging
import re

import exchangerates
import hxl
from hdx.location.country import Country
from hdx.utilities.dateparse import parse_date
from hdx.utilities.loader import load_json


logger = logging.getLogger(__name__)


def clean_string(s):
    """ Normalise whitespace in a single, and remove any punctuation at the start/end """
    s = re.sub(r'^\W*(\w.*)\W*$', r'\1', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


class Lookups:
    org_names = dict()
    default_org = None
    sector_info = None
    default_sector = None
    default_country = None
    fx_rates = None
    fallback_rates = None
    filter_reporting_orgs = list()
    filter_reporting_orgs_children = list()

    @classmethod
    def setup(cls, configuration, retriever):
        logger.info('Reading in lookups data')
        org_data = load_json(configuration['org_data'])
        """ Map from IATI identifiers to organisation names """
        # Prime with org identifiers from code4iati
        for entry in org_data['data']:
            code = clean_string(entry['code']).lower()
            cls.org_names[code] = clean_string(entry['name'])
        cls.sector_info = load_json(configuration['sector_data'])
        cls.default_org = configuration['default_org']
        cls.default_sector = configuration['default_sector']
        cls.default_country = configuration['default_country']
        rates_path = retriever.retrieve_file(configuration['rates_url'], 'rates.csv', 'exchange rates', True)
        cls.fx_rates = exchangerates.CurrencyConverter(update=False, source=rates_path)
        rjson = retriever.retrieve_json(configuration['fallback_rates_url'], 'fallbackrates.json',
                                        'fallback exchange rates', True)
        cls.fallback_rates = rjson['rates']
        for row in hxl.data(configuration['filters_url']):
            org_id = row.get('#org+reporting+id')
            if org_id:
                cls.filter_reporting_orgs.append(org_id)
            org_id = row.get('#org+reporting_children+id')
            if org_id:
                cls.filter_reporting_orgs_children.append(org_id)

    @classmethod
    def is_filter_reporting_orgs(cls, orgid):
        return True if orgid in cls.filter_reporting_orgs else False

    @classmethod
    def is_filter_reporting_orgs_children(cls, orgid):
        return True if orgid in cls.filter_reporting_orgs_children else False

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

    @classmethod
    def get_value_in_usd(cls, value, currency, date):
        if currency == 'USD':
            return value
        try:
            fx_rate = cls.fx_rates.closest_rate(currency, parse_date(date).date()).get('conversion_rate')
        except exchangerates.UnknownCurrencyException:
            fx_rate = cls.fallback_rates.get(currency)
            if fx_rate is None:
                logger.exception(f'Currency {currency} is invalid!')
                return 0
        return value / fx_rate
