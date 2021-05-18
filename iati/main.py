# -*- coding: utf-8 -*-
import logging
from io import StringIO
from os.path import join
from urllib.parse import quote

import diterator
import hxl
from hdx.utilities.dictandlist import write_list_to_csv
from hdx.utilities.saver import save_json

from iati.activity import Activity
from iati.calculatesplits import CalculateSplits
from iati.fxrates import FXRates
from iati.lookups import Lookups

logger = logging.getLogger(__name__)


def retrieve_dportal(configuration, retriever, dportal_params):
    """
    Downloads activity data from D-Portal. Filters them and returns a
    list of activities.
    """
    dportal_configuration = configuration['dportal']
    base_filename = dportal_configuration['filename']
    dportal_limit = dportal_configuration['limit']
    n = 0
    dont_exit = True
    while dont_exit:
        if dportal_params:
            params = dportal_params
            dont_exit = False
        else:
            offset = n * dportal_limit
            params = f'LIMIT {dportal_limit} OFFSET {offset}'
            logger.info(f'OFFSET {offset}')
        url = dportal_configuration['url'] % quote(dportal_configuration['query'].format(params))
        filename = base_filename.format(n)
        text = retriever.retrieve_text(url, filename, 'D-Portal activities', False)
        if '<iati-activity' in text:
            n += 1
            yield text
        else:
            # If the result doesn't contain any IATI activities, we're done
            dont_exit = False


def should_ignore_activity(activity):
    return False


def start(configuration, this_month, retriever, dportal_params):
    fx = FXRates(configuration['fxrates'], retriever)
    generator = retrieve_dportal(configuration, retriever, dportal_params)
    # Build the accumulators from the IATI activities and transactions
    Lookups.setup(configuration)
    CalculateSplits.setup(configuration)
    transactions = list()
    flows = list()
    for text in generator:
        for dactivity in diterator.XMLIterator(StringIO(text)):
            activity = Activity(configuration, this_month, dactivity)

            if not activity.should_process():
                continue

            activity_transactions, activity_flows = activity.process()
            transactions.extend(activity_transactions)
            flows.extend(activity_flows)

    logger.info(f'Processed {len(transactions)} transactions')
    logger.info(f'Processed {len(flows)} flows')

    outputs_configuration = configuration['outputs']
    output_dir = outputs_configuration['folder']
    #
    # Write transactions
    #
    transactions_configuration = outputs_configuration['transactions']

    # Add headers and sort the transactions.
    headers = transactions_configuration['headers']
    hxltags = transactions_configuration['hxltags']
    transactions = [headers, hxltags] + sorted(transactions)

    # Write the JSON
    save_json(transactions, join(output_dir, transactions_configuration['json']))

    # Write the CSV
    write_list_to_csv(join(output_dir, transactions_configuration['csv']), transactions)

    #
    # Prepare and write flows
    #
    flows_configuration = outputs_configuration['flows']

    # Add headers and aggregate
    headers = flows_configuration['headers']
    hxltags = flows_configuration['hxltags']
    rows = [headers, hxltags]
    flows = hxl.data(rows + flows).count(
        rows[1][:-1],  # make a list of patterns from all but the last column of the hashtag row
        aggregators='sum(#value+total) as Total money#value+total'
    ).cache()

    # Write the JSON
    with open(join(output_dir, flows_configuration['json']), 'w') as output:
        for line in flows.gen_json():
            print(line, file=output, end="")

    # Write the CSV
    with open(join(output_dir, flows_configuration['csv']), 'w') as output:
        for line in flows.gen_csv():
            print(line, file=output, end="")
