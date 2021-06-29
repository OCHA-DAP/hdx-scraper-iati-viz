# -*- coding: utf-8 -*-
import logging
import re
from os.path import join

import exchangerates
import hxl
from hdx.location.country import Country
from hdx.utilities.dateparse import parse_date
from hdx.utilities.loader import load_json
from hdx.utilities.saver import save_json

logger = logging.getLogger(__name__)


def clean_string(s):
    """ Normalise whitespace in a single, and remove any punctuation at the start/end """
    s = re.sub(r'^\W*(\w.*)\W*$', r'\1', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


class Lookups:
    org_ref_blocklist = list()
    org_ref_to_name = dict()
    org_ref_to_type = dict()
    org_names_to_ref = dict()
    org_names_to_type = dict()
    orgs_lookedup = set()
    default_org_id = None
    default_org_name = None
    default_expenditure_org_name = None
    default_all_org_names = list()
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
            name = clean_string(entry['name'])
            cls.org_ref_to_name[code] = name
            cls.org_names_to_ref[name.lower()] = code
        cls.sector_info = load_json(configuration['sector_data'])
        cls.default_org_id = configuration['default_org_id']
        cls.default_org_name = configuration['default_org_name']
        cls.default_all_org_names.append(cls.default_org_name)
        cls.default_expenditure_org_name = configuration['default_expenditure_org_name']
        cls.default_all_org_names.append(cls.default_expenditure_org_name)

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
        for row in hxl.data(configuration['blocklist_url']):
            org_id = row.get('#org+reporting+id')
            if org_id:
                cls.org_ref_blocklist.append(org_id)

    @classmethod
    def is_filter_reporting_orgs(cls, orgid):
        return True if orgid in cls.filter_reporting_orgs else False

    @classmethod
    def is_filter_reporting_orgs_children(cls, orgid):
        return True if orgid in cls.filter_reporting_orgs_children else False

    @staticmethod
    def get_cleaned_ref_name_type(org):
        ref = None if org is None or org.ref is None else clean_string(str(org.ref)).lower()
        other_names = list()
        orig_name = None
        org_name = None
        org_type = None
        if org:
            if org.name:
                orig_name = clean_string(str(org.name))
                for key, value in org.name.narratives.items():
                    value = clean_string(value)
                    if value:
                        if key.lower() == 'en':
                            org_name = value
                        else:
                            other_names.append(value)
            if org.type:
                org_type = org.type
        names = list()
        if org_name:
            names.append(org_name)
        if orig_name and orig_name not in names:
            names.append(orig_name)
        if other_names:
            [names.append(x) for x in other_names if x not in names]
        return ref, names, org_type

    @classmethod
    def add_to_org_lookup(cls, org, is_participating_org=False):
        ref, names, org_type = cls.get_cleaned_ref_name_type(org)
        for name in names:
            lower_name = name.lower()
            cur_ref = cls.org_names_to_ref.get(lower_name)
            if cur_ref:
                if cur_ref not in cls.org_ref_to_name:
                    cls.org_ref_to_name[cur_ref] = name
            if ref:
                if is_participating_org and ref in cls.org_ref_blocklist:
                    continue
                if cur_ref:
                    if ref not in cls.org_ref_to_name:
                        cls.org_ref_to_name[ref] = cls.org_ref_to_name[cur_ref]
                else:
                    if ref not in cls.org_ref_to_name:
                        cls.org_ref_to_name[ref] = name
                    cls.org_names_to_ref[lower_name] = ref
                if org_type and lower_name not in cls.org_names_to_type:
                    cls.org_names_to_type[lower_name] = org_type
            elif org_type and lower_name not in cls.org_names_to_type:
                cls.org_names_to_type[lower_name] = org_type
        if org_type:
            if is_participating_org and ref and ref in cls.org_ref_blocklist:
                return
            if ref and ref not in cls.org_ref_to_type:
                cls.org_ref_to_type[ref] = org_type

    @classmethod
    def get_org_info(cls, org, reporting_org=False, expenditure=False):
        """ Standardise organisation names
        For now, use the first name found for an identifier.
        Later, we can reference the registry.
        """
        if expenditure:
            default_org_name = cls.default_expenditure_org_name
        else:
            default_org_name = cls.default_org_name
        ref, names, org_type = cls.get_cleaned_ref_name_type(org)

        refs = list()
        if ref:
            refs.append(ref)
        for name in names:
            if name:
                associated_ref = cls.org_names_to_ref.get(name.lower())
                if associated_ref and associated_ref not in refs:
                    refs.append(associated_ref)
        # In case ref is being misused as a name
        if ref and not names:
            ref = cls.org_names_to_ref.get(ref.lower(), ref)
            if ref and ref not in refs:
                refs.append(ref)
        ref = None
        preferred_name = None
        i = 0
        while i != len(refs):
            ref_to_consider = refs[i]
            if not reporting_org and ref_to_consider in cls.org_ref_blocklist:
                i += 1
                continue
            preferred_name = cls.org_ref_to_name.get(ref_to_consider)
            if preferred_name:
                ref = ref_to_consider
                break
            i += 1
        if not ref:
            if refs:
                ref = refs[0]
            else:
                ref = cls.default_org_id
        if preferred_name:
            name = preferred_name
        elif names:
            name = names[0]
        else:
            name = default_org_name

        preferred_type = None
        if ref and ref != cls.default_org_id:
            if reporting_org:
                if name != default_org_name:
                    cls.orgs_lookedup.add((ref, name))
            elif ref in cls.org_ref_blocklist and name and name != default_org_name:
                ref = cls.org_names_to_ref.get(name.lower())
            if ref:
                preferred_type = cls.org_ref_to_type.get(ref)
        if not preferred_type and name and name != default_org_name:
            preferred_type = cls.org_names_to_type.get(name.lower())
        if preferred_type:
            org_type = preferred_type
        return {'id': ref, 'name': name, 'type': org_type}

    # This can be used to get a list of org refs to check to see if they should be added to the manual list
    # @classmethod
    # def build_reporting_org_blocklist(cls, dactivities):
    #     ref_to_names = dict()
    #     for dactivity in dactivities:
    #         for org in dactivity.participating_orgs:
    #             ref, name, _ = cls.get_cleaned_ref_name_type(org)
    #             if ref and name:
    #                 dict_of_sets_add(ref_to_names, ref, name)
    #     for ref, names in ref_to_names.items():
    #         if len(names) > 5:
    #             cls.org_ref_blocklist.append(ref)

    @classmethod
    def add_reporting_orgs(cls, dactivities):
        for dactivity in reversed(dactivities):
            cls.add_to_org_lookup(dactivity.reporting_org)

    @classmethod
    def add_participating_orgs(cls, dactivities):
        for dactivity in reversed(dactivities):
            for org in dactivity.participating_orgs:
                cls.add_to_org_lookup(org, is_participating_org=True)

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
