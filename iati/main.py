# -*- coding: utf-8 -*-
import json
import logging
from io import StringIO
from os.path import join
from urllib.parse import quote

import diterator
import unicodecsv

from iati.activity import Activity
from iati.calculatesplits import CalculateSplits
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


def write(configuration, configuration_key, rows):
    output_dir = configuration['folder']
    file_configuration = configuration[configuration_key]
    headers = file_configuration['headers']
    hxltags = file_configuration['hxltags']

    with open(join(output_dir, file_configuration['csv']), 'wb') as output_csv:
        writer = unicodecsv.writer(output_csv, encoding='utf-8')
        writer.writerow(headers)
        writer.writerow(hxltags)
        with open(join(output_dir, file_configuration['json']), 'w') as output_json:
            output_json.write('[')

            def write_row(inrow, ending):
                writer.writerow(inrow)
                row = {hxltag: inrow[i] for i, hxltag in enumerate(hxltags)}
                output_json.write(json.dumps(row, indent=None, separators=(',', ':')) + ending)

            [write_row(row, ',\n') for row in rows[:-1]]
            write_row(rows[-1], ']')


def start(configuration, this_month, retriever, dportal_params):
    generator = retrieve_dportal(configuration, retriever, dportal_params)
    Lookups.setup(configuration['lookups'], retriever)
    CalculateSplits.setup(configuration['calculate_splits'])

    # Build the accumulators from the IATI activities and transactions
    flows = dict()
    transactions = list()
    for text in generator:
        for dactivity in diterator.XMLIterator(StringIO(text)):
            activity = Activity(configuration, this_month, dactivity)
            if activity.should_ignore():
                continue
            activity.setup()
            activity.process(flows, transactions)

    logger.info(f'Processed {len(flows)} flows')
    logger.info(f'Processed {len(transactions)} transactions')

    outputs_configuration = configuration['outputs']

    #
    # Prepare and write flows
    #
    write(outputs_configuration, 'flows', [list(key)+[int(round(flows[key]))] for key in sorted(flows)])

    #
    # Write transactions
    #
    write(outputs_configuration, 'transactions', sorted(transactions))
