# -*- coding: utf-8 -*-
#
# Utility functions
#
import json
import re

from hdx.utilities.loader import load_json


#
# Constants
#

DEFAULT_ORG = "(unspecified org)"

TRANSACTIONS_JSON = "transactions.json"

TRANSACTIONS_CSV = "transactions.csv"

TRANSACTION_HEADERS = [
    [
        "Month",
        "Reporting org",
        "Reporting org type",
        "Sector",
        "Recipient country",
        "Humanitarian?",
        "Strict?",
        "Transaction type",
        "Activity id",
        "Net money",
        "Total money"
    ],
    [
        "#date+month",
        "#org+name",
        "#org+type",
        "#sector",
        "#country",
        "#indicator+bool+humanitarian",
        "#indicator+bool+strict",
        "#x_transaction_type",
        "#activity+code",
        "#value+net",
        "#value+total"
    ],
]


FLOWS_JSON = "flows.json"

FLOWS_CSV = "flows.csv"

FLOW_HEADERS = [
    [
        "Reporting org",
        "Reporting org type",
        "Provider org",
        "Receiver org",
        "Humanitarian?",
        "Strict?",
        "Transaction type",
        "Transaction direction",
        "Total money",
    ],
    [
        "#org+name+reporting",
        "#org+reporting+type",
        "#org+name+provider",
        "#org+name+receiver",
        "#indicator+bool+humanitarian",
        "#indicator+bool+strict",
        "#x_transaction_type",
        "#x_transaction_direction",
        "#value+total"
    ],
]

TRANSACTION_TYPE_INFO = {
    "1": {
        "label": "Incoming Funds",
        "classification": "spending",
        "direction": "incoming",
    },
    "2": {
        "label": "Outgoing Commitment",
        "classification": "commitments",
        "direction": "outgoing",
    },
    "3": {
        "label": "Disbursement",
        "classification": "spending",
        "direction": "outgoing",
    },
    "4": {
        "label": "Expenditure",
        "classification": "spending",
        "direction": "outgoing",
    },
    "11": {
        "label": "Incoming Commitment",
        "classification": "commitments",
        "direction": "incoming",
    },
}

#
# Global variables
#

json_files = {}
""" Cache for loaded JSON files """

org_names = None
""" Map from IATI identifiers to organisation names """


#
# Utility functions
#

def load_json (filename):
    """ Load a JSON file if not already in memory, then return it """
    global json_files
    if not filename in json_files:
        with open(filename, "r") as input:
            json_files[filename] = json.load(input)
    return json_files[filename]


def clean_string (s):
    """ Normalise whitespace in a single, and remove any punctuation at the start/end """
    s = re.sub(r'^\W*(\w.*)\W*$', r'\1', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def get_org_name (org):
    """ Standardise organisation names
    For now, use the first name found for an identifier.
    Later, we can reference the registry.
    """
    global org_names

    # Prime with org identifiers from code4iati
    if org_names is None:
        map = load_json("data/IATIOrganisationIdentifier.json")
        org_names = {}
        for entry in map["data"]:
            code = clean_string(entry["code"]).lower()
            org_names[code] = clean_string(entry["name"])

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
    return DEFAULT_ORG


def get_sector_group_name (code):
    """ Look up a group name for a 3- or 5-digit sector code.
    """
    sector_info = load_json("data/dac3-sector-map.json")
    code = code[:3]
    if code in sector_info:
        return sector_info.get(code)["dac-group"]
    else:
        return "(Unspecified sector)"


def get_country_name (code):
    country_info = load_json("data/countries.json")
    for info in country_info["data"]:
        if info["iso2"] == code:
            return info["label"]["default"]
    return "(Unspecified country)"


def convert_to_usd (value, source_currency, isodate):
    # FIXME not using date
    source_currency = source_currency.upper().strip()
    if value != 0.0 and source_currency != "USD":
        rates = load_json("data/fallbackrates.json")
        if source_currency in rates["rates"]:
            value /= rates["rates"][source_currency]
        else:
            value = 0
    return int(round(value))