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