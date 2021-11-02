import glob
import logging
from os.path import join

import diterator
from hdx.location.currency import Currency
from hdx.utilities.downloader import Download
from hdx.utilities.retriever import Retrieve
from natsort import natsorted

from iati import checks
from iati.activity import Activity
from iati.calculatesplits import CalculateSplits
from iati.data import is_xml, write, dactivity_iterator
from iati.lookups import Lookups

logger = logging.getLogger(__name__)


def start(
    configuration, today, output_dir, data_dir, whattorun, filterdate, downloader=None
):
    retriever = Retrieve(
        downloader or Download(),
        configuration["fallback_dir"],
        data_dir,
        output_dir,
        False,
        True,
    )
    if filterdate:
        text = f"removing transactions before {filterdate}"
    else:
        text = "without removing transactions before a certain date"
    logger.info(f"Running {whattorun} {text}")
    Lookups.checks = checks[whattorun]
    Lookups.filter_transaction_date = filterdate
    Lookups.setup(configuration["lookups"])
    Currency.setup(
        retriever=retriever,
        fallback_historic_to_current=True,
        fallback_current_to_static=True,
    )
    CalculateSplits.setup(configuration["calculate_splits"])

    # Build org name lookup
    #    Lookups.build_reporting_org_blocklist()
    Lookups.add_reporting_orgs(data_dir)
    Lookups.add_participating_orgs(data_dir)

    # Build the accumulators from the IATI activities and transactions
    flows = dict()
    transactions = list()
    all_skipped = 0
    for i, dactivity in enumerate(dactivity_iterator(data_dir)):
        activity, skipped = Activity.get_activity(configuration, dactivity)
        all_skipped += skipped
        if activity:
            all_skipped += activity.process(today[:7], flows, transactions)
        if i % 1000 == 0:
            logger.info(f"Processed {i} activities")

    logger.info(f"Processed {len(flows)} flows")
    logger.info(f"Processed {len(transactions)} transactions")
    logger.info(f"Skipped {all_skipped} transactions")

    outputs_configuration = configuration["outputs"]

    # Prepare and write flows
    write(
        today,
        output_dir,
        outputs_configuration,
        "flows",
        [
            flows[key]["row"] + [int(round(flows[key]["value"]))]
            for key in sorted(flows)
        ],
    )

    # Write transactions
    write(
        today,
        output_dir,
        outputs_configuration,
        "transactions",
        sorted(
            transactions,
            key=lambda x: (x[0], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10]),
        ),
        all_skipped,
    )

    # Write orgs
    write(
        today,
        output_dir,
        outputs_configuration,
        "orgs",
        sorted(Lookups.used_reporting_orgs, key=lambda x: (x[1], x[0])),
    )
