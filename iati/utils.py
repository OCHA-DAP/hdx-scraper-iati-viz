# -*- coding: utf-8 -*-
#
# Utility functions
#
import re

from hdx.location.country import Country
from hdx.utilities.loader import load_json


def clean_string(s):
    """ Normalise whitespace in a single, and remove any punctuation at the start/end """
    s = re.sub(r'^\W*(\w.*)\W*$', r'\1', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


#
# Global variables
#
org_data = load_json("data/IATIOrganisationIdentifier.json")
org_names = {}
""" Map from IATI identifiers to organisation names """
# Prime with org identifiers from code4iati
for entry in org_data["data"]:
    code = clean_string(entry["code"]).lower()
    org_names[code] = clean_string(entry["name"])
sector_info = load_json("data/dac3-sector-map.json")


#
# Utility functions
#
def get_org_name(org, default_org):
    """ Standardise organisation names
    For now, use the first name found for an identifier.
    Later, we can reference the registry.
    """
    name = None if org is None or org.name is None else clean_string(str(org.name))
    ref = None if org is None or org.ref is None else clean_string(str(org.ref)).lower()

    # We have a ref and an existing match
    if ref and ref in org_names:
        # existing match
        return org_names[ref]

    # No existing match, but we have a name
    if name:
        if ref is not None:
            # if there's a ref, save it for future matching
            org_names[ref] = name
        return name

    # We can't figure out anything
    return default_org


def get_sector_group_name(code):
    """ Look up a group name for a 3- or 5-digit sector code.
    """
    code = code[:3]
    if code in sector_info:
        return sector_info.get(code)["dac-group"]
    else:
        return "(Unspecified sector)"


def get_country_name(code):
    countryname = Country.get_country_name_from_iso2(code)
    if countryname:
        return countryname
    return "(Unspecified country)"


def convert_to_usd(value, source_currency, isodate):
    # FIXME not using date
    source_currency = source_currency.upper().strip()
    if value != 0.0 and source_currency != "USD":
        rates = load_json("data/fallbackrates.json")
        if source_currency in rates["rates"]:
            value /= rates["rates"][source_currency]
        else:
            value = 0
    return int(round(value))