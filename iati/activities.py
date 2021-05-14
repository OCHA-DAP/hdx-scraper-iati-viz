# -*- coding: utf-8 -*-
import logging
from io import StringIO
from datetime import datetime

import diterator


#
# Business-logic functions
#
from iati.utils import get_org_name, TRANSACTION_TYPE_INFO, convert_to_usd, get_sector_group_name, get_country_name, \
    DEFAULT_ORG


def make_country_splits(entity, default_splits=None, default_country="XX"):
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


def make_sector_splits(entity, default_splits=None, default_sector="99999"):
    """ Generate sector splits by percentage for an activity or transaction
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


def has_c19_scope(scopes):
    """ Check if the COVID-19 GLIDE number or HRP code is present """
    for scope in scopes:
        if scope.type == "1" and scope.vocabulary == "1-2" and scope.code.upper() == "EP-2020-000012-001":
            return True
        elif scope.type == "2" and scope.vocabulary == "2-1" and scope.code.upper() == "HCOVD20":
            return True
    return False


def has_c19_tag(tags):
    """ Check if the COVID-19 tag is present """
    for tag in tags:
        if tag.vocabulary == "99" and tag.code.upper() == "COVID-19":
            return True
    return False


def has_c19_sector(sectors):
    """ Check if the DAC COVID-19 sector code is present """
    for sector in sectors:
        if sector.vocabulary == "1" and sector.code == "12264":
            return True
    return False


def is_c19_narrative(narratives):
    """ Check a dict of different-language text for the string "COVID-19" (case-insensitive) """
    for lang, text in narratives.items():
        if "COVID-19" in text.upper():
            return True
    return False


def is_activity_strict(activity):
    return True if (
            has_c19_scope(activity.humanitarian_scopes) or
            has_c19_tag(activity.tags) or
            has_c19_sector(activity.sectors) or
            is_c19_narrative(activity.title.narratives)
    ) else False


def is_transaction_strict(transaction):
    return True if (
            has_c19_sector(transaction.sectors) or
            (transaction.description and is_c19_narrative(transaction.description.narratives))
    ) else False


def sum_transactions(transactions, types):
    total = 0
    for transaction in transactions:
        if transaction.value is None:
            continue
        elif transaction.type in types:
            total += convert_to_usd(transaction.value, transaction.currency, transaction.date)
    return total


def process_activities(generator):

    transactions = list()

    flows = list()

    activities_seen = set()

    this_month = datetime.utcnow().isoformat()[:7]

    for text in generator:
        for activity in diterator.XMLIterator(StringIO(text)):

            # Don't use the same activity twice
            identifier = activity.identifier
            if identifier in activities_seen:
                continue
            activities_seen.add(identifier)

            # Skip activities from a secondary reporter (should have been filtered out already)
            if activity.secondary_reporter:
                continue

            # Get the reporting-org name and C19 strictness at activity level
            org = get_org_name(activity.reporting_org)
            org_type = str(activity.reporting_org.type)
            activity_strict = is_activity_strict(activity)

            # Figure out default country/sector percentage splits at the activity level
            activity_country_splits = make_country_splits(activity)
            activity_sector_splits = make_sector_splits(activity)

            #
            # Figure out how to factor new money
            #

            # Total up the 4 kinds of transactions (with currency conversion to USD)
            incoming_funds = sum_transactions(activity.transactions, ["1"])
            outgoing_commitments = sum_transactions(activity.transactions, ["2"])
            spending = sum_transactions(activity.transactions, ["3", "4"])
            incoming_commitments = sum_transactions(activity.transactions, ["11"])

            # Figure out total incoming money (never less than zero)
            incoming = max(incoming_commitments, incoming_funds)
            if incoming < 0:
                incoming = 0

            # Factor to apply to outgoing commitments for net new money
            if incoming == 0:
                commitment_factor = 1.0
            elif outgoing_commitments > incoming:
                commitment_factor = (outgoing_commitments - incoming) / outgoing_commitments
            else:
                commitment_factor = 0.0

            # Factor to apply to outgoing spending for net new money
            if incoming == 0:
                spending_factor = 1.0
            elif spending > incoming:
                spending_factor = (spending - incoming) / spending
            else:
                spending_factor = 0.0


            #
            # Walk through the activity's transactions one-by-one, and split by country/sector
            #

            for transaction in activity.transactions:

                month = transaction.date[:7]
                if month < "2020-01" or month > this_month or not transaction.value:
                    # Skip transactions with no values or with out-of-range months
                    continue

                type = transaction.type
                if type in TRANSACTION_TYPE_INFO:
                    type_info = TRANSACTION_TYPE_INFO[type]
                else:
                    # skip transaction types that don't interest us
                    continue

                # Convert the transaction value to USD
                value = convert_to_usd(transaction.value, transaction.currency, transaction.date)

                # Set the net (new money) factors based on the type (commitments or spending)
                if type_info["direction"] == "outgoing":
                    if type_info["classification"] == "commitments":
                        net_value = value * commitment_factor
                    else:
                        net_value = value * spending_factor

                # transaction status defaults to activity
                if transaction.humanitarian is None:
                    is_humanitarian = activity.humanitarian
                else:
                    is_humanitarian = transaction.humanitarian
                is_strict = activity_strict or is_transaction_strict(transaction)

                # Make the splits for the transaction (default to activity splits)
                country_splits = make_country_splits(transaction, activity_country_splits)
                sector_splits = make_sector_splits(transaction, activity_sector_splits)


                # Apply the country and sector percentage splits to the transaction
                # generate multiple split transactions
                for country, country_percentage in country_splits.items():
                    for sector, sector_percentage in sector_splits.items():

                        sector_name = get_sector_group_name(sector)
                        country_name = get_country_name(country)

                        #
                        # Add to transactions
                        #

                        net_money = int(round(net_value * country_percentage * sector_percentage))
                        total_money = int(round(value * country_percentage * sector_percentage))

                        # Fill in only if we end up with a non-zero value
                        if type_info["direction"] == "outgoing" and (net_money != 0 or total_money != 0):

                            # add to transactions
                            transactions.append([
                                month,
                                org,
                                org_type,
                                sector_name,
                                country_name,
                                1 if is_humanitarian else 0,
                                1 if is_strict else 0,
                                type_info["classification"],
                                identifier,
                                net_money,
                                total_money,
                            ])

                    #
                    # Add to flows
                    #
                    if type_info["direction"] == "incoming":
                        provider = get_org_name(transaction.provider_org)
                        receiver = None
                    else:
                        provider = None
                        receiver = get_org_name(transaction.receiver_org)
                    if org != provider and org != receiver and org != DEFAULT_ORG:
                        # ignore internal transactions or unknown reporting orgs
                        flows.append([
                            org,
                            org_type,
                            provider,
                            receiver,
                            1 if is_humanitarian else 0,
                            1 if is_strict else 0,
                            type_info["classification"],
                            type_info["direction"],
                            total_money
                        ])

    return transactions, flows
