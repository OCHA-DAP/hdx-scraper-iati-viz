# -*- coding: utf-8 -*-
import logging
from os import mkdir
from os.path import join
from shutil import rmtree
from urllib.parse import quote

import hxl
from hdx.utilities.dictandlist import write_list_to_csv
from hdx.utilities.saver import save_json

from iati.activities import process_activities
from iati.fxrates import FXRates
from iati.utils import TRANSACTION_HEADERS, TRANSACTIONS_JSON, TRANSACTIONS_CSV, FLOWS_JSON, FLOWS_CSV, FLOW_HEADERS

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


def start(configuration, retriever, outputs, tabs, dportal_params, temp_folder):
    def update_tab(name, data):
        logger.info('Updating tab: %s' % name)
        for output in outputs.values():
            output.update_tab(name, data)

    fx = FXRates(configuration['fxrates'], retriever)
    output_dir = join(temp_folder, 'output_data')
    rmtree(output_dir, ignore_errors=True)
    mkdir(output_dir)
    generator = retrieve_dportal(configuration, retriever, dportal_params)
    # Build the accumulators from the IATI activities and transactions
    transactions, flows = process_activities(generator)
    logger.info(f'Processed {len(transactions)} transactions')
    logger.info(f'Processed {len(flows)} flows')

    #
    # Write transactions
    #

    # Add headers and sort the transactions.
    transactions = TRANSACTION_HEADERS + sorted(transactions)

    # Write the JSON
    save_json(transactions, join(output_dir, TRANSACTIONS_JSON))

    # Write the CSV
    write_list_to_csv(join(output_dir, TRANSACTIONS_CSV), transactions)

    #
    # Prepare and write flows
    #

    # Add headers and aggregate
    flows = hxl.data(FLOW_HEADERS + flows).count(
        FLOW_HEADERS[1][:-1], # make a list of patterns from all but the last column of the hashtag row
        aggregators="sum(#value+total) as Total money#value+total"
    ).cache()

    # Write the JSON
    with open(join(output_dir, FLOWS_JSON), "w") as output:
        for line in flows.gen_json():
            print(line, file=output, end="")

    # Write the CSV
    with open(join(output_dir, FLOWS_CSV), "w") as output:
        for line in flows.gen_csv():
            print(line, file=output, end="")

# end
#    update_tab('commitmentsspending', commitments_spending)
#    update_tab('activitytotals', activity_counts)
