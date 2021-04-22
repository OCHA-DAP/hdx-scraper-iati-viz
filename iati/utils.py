# -*- coding: utf-8 -*-
#
# Utility functions
#
import re

from hdx.utilities.loader import load_json


def clean_string(s):
    """ Normalise whitespace in a single, and remove any punctuation at the start/end """
    s = re.sub(r'^\W*(\w.*)\W*$', r'\1', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()


def pack_key(parts):
    return (
        parts['month'],
        parts['org'],
        parts['country'],
        parts['sector'],
        parts['is_humanitarian'],
        parts['is_strict'],
    )


def unpack_key(key):
    return {
        'month': key[0],
        'org': key[1],
        'country': key[2],
        'sector': key[3],
        'is_humanitarian': key[4],
        'is_strict': key[5],
    }

def convert_to_usd(value, source_currency, isodate):
    # FIXME not using date
    value = float(value)
    source_currency = source_currency.upper().strip()
    if source_currency != "USD":
        rates = load_json("data/fallbackrates.json")
        if source_currency in rates["rates"]:
            value /= rates["rates"][source_currency]
        else:
            value = 0
    return int(round(value))

