import logging
from os import remove
from os.path import join
from urllib.parse import quote

import diterator
from hdx.location.currency import Currency
from hdx.utilities.dateparse import parse_date
from hdx.utilities.saver import save_hxlated_output

from . import checks
from .activity import Activity
from .calculatesplits import CalculateSplits
from .lookups import Lookups
from .smalldactivity import create_small_dactivity

logger = logging.getLogger(__name__)


def retrieve_dportal(retriever, whattorun, dportal_params=""):
    """
    Downloads activity data from D-Portal. Filters them and returns a
    list of activities.
    """
    dportal_configuration = Lookups.configuration["dportal"]
    filename = dportal_configuration["filename"]
    url = dportal_configuration["url"] % quote(
        dportal_configuration[f"{whattorun}_query"].format(dportal_params)
    )
    return filename, retriever.download_file(
        url, filename, "D-Portal activities", False
    )


def start(
    configuration,
    today,
    retriever,
    output_dir,
    dportal_params,
    whattorun,
    startdate,
    saveprefiltered,
    errors_on_exit,
):
    if startdate:
        text = f"removing activities and transactions before {startdate}"
    else:
        text = "with no date filtering"
    logger.info(f"Running {whattorun} {text}")
    Lookups.configuration = configuration
    if startdate is not None:
        startdate = parse_date(startdate)
    Lookups.checks = checks[whattorun](parse_date(today), startdate, errors_on_exit)
    dportal_filename, dportal_path = retrieve_dportal(
        retriever, whattorun, dportal_params
    )
    Lookups.setup()
    Currency.setup(
        retriever=retriever,
        fallback_historic_to_current=True,
        fallback_current_to_static=True,
    )
    CalculateSplits.setup()

    # Build org name lookup
    logger.info("Reading activities")
    xmliterator = diterator.XMLIterator(dportal_path)
    prefiltered_path = join(output_dir, "prefiltered.xml")
    writer = open(prefiltered_path, "w")
    writer.write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<iati-activities xmlns:ns0="http://d-portal.org/xmlns/dstore" xmlns:ns1="http://d-portal.org/xmlns/iati-activities" xmlns:ns2="xml" version="2.03">\n'
    )
    no_query_activities = 0
    no_removed_activities = 0
    no_removed_transactions = 0
    for dactivity in xmliterator:
        no_query_activities += 1
        if no_query_activities % 1000 == 0:
            logger.info(f"Read {no_query_activities} activities")
        exclude, removed_transactions = Lookups.checks.exclude_activity(dactivity)
        if exclude:
            del dactivity
            no_removed_activities += 1
            continue
        no_removed_transactions += len(removed_transactions)
        activity_node = dactivity.node
        transaction_nodes = dactivity.get_nodes("transaction")
        for i in removed_transactions:
            activity_node.removeChild(transaction_nodes[i])
        writer.write(activity_node.toxml())
        del dactivity
    writer.write("\n</iati-activities>")
    writer.close()
    del xmliterator  # Maybe this helps garbage collector?
    logger.info(f"D-Portal returned {no_query_activities} activities")
    if no_removed_activities == 0:
        logger.info(f"Activity Prefiltering did not remove any activities")
    else:
        logger.info(f"Activity Prefiltering removed {no_removed_activities} activities")
        no_remaining = no_query_activities - no_removed_transactions
        logger.info(f"{no_remaining} activities after Activity Prefiltering")
    logger.info(
        f"Activity Prefiltering removed {no_removed_transactions} from within remaining activities"
    )

    xmliterator = diterator.XMLIterator(prefiltered_path)
    #    Lookups.build_reporting_org_blocklist(dactivities)
    Lookups.add_reporting_orgs(xmliterator)
    logger.info("Added reporting orgs to lookup")
    del xmliterator  # Maybe this helps garbage collector?
    xmliterator = diterator.XMLIterator(prefiltered_path)
    Lookups.add_participating_orgs(xmliterator)
    logger.info("Added participating orgs to lookup")
    del xmliterator  # Maybe this helps garbage collector?

    # Build the accumulators from the IATI activities and transactions
    logger.info("Processing activities")
    xmliterator = diterator.XMLIterator(prefiltered_path)
    flows = dict()
    transactions = list()
    no_unvaluable_activities = 0
    no_unvaluable_transactions = 0
    no_skipped_transactions = 0
    no_incoming_transactions = 0
    for i, full_dactivity in enumerate(xmliterator):
        dactivity = create_small_dactivity(full_dactivity)
        del full_dactivity
        (
            no_valued_transactions,
            unvaluable_transactions,
        ) = Lookups.checks.exclude_transactions(dactivity)
        if no_valued_transactions == 0:
            no_unvaluable_activities += 1
            continue
        no_unvaluable_transactions += unvaluable_transactions
        activity = Activity(dactivity)
        skipped, incoming = activity.process(flows, transactions)
        no_skipped_transactions += skipped
        no_incoming_transactions += incoming
        if i % 1000 == 0:
            logger.info(f"Processed {i} activities")
    del xmliterator
    logger.info(
        f"Processing found {no_unvaluable_activities} activities with no transactions that could be valued"
    )
    logger.info(
        f"Processing found {no_unvaluable_transactions} transactions that could not be valued from within remaining activities"
    )
    logger.info(f"Processed {len(flows)} flows")
    logger.info(f"Processed {len(transactions)} transactions")
    logger.info(f"{no_skipped_transactions} transactions were skipped")
    logger.info(f"{no_incoming_transactions} incoming transactions (no net value)")

    outputs_configuration = configuration["outputs"]

    # Prepare and write flows
    logger.info(f"Writing flows files to {output_dir}")
    out_flows = [
        flows[key]["row"] + [int(round(flows[key]["value"]))] for key in sorted(flows)
    ]
    save_hxlated_output(
        outputs_configuration["flows"],
        out_flows,
        includes_header=False,
        includes_hxltags=False,
        output_dir=output_dir,
        today=today,
        num_flows=len(out_flows),
    )

    # Write transactions
    logger.info(f"Writing transactions files to {output_dir}")
    out_transactions = sorted(
        transactions,
        key=lambda x: (x[0], x[2], x[3], x[4], x[5], x[6], x[7], x[8], x[9], x[10]),
    )
    save_hxlated_output(
        outputs_configuration["transactions"],
        out_transactions,
        includes_header=False,
        includes_hxltags=False,
        output_dir=output_dir,
        today=today,
        num_transactions=len(out_transactions),
    )

    # Write orgs
    logger.info(f"Writing orgs files to {output_dir}")
    orgs = sorted(Lookups.used_reporting_orgs, key=lambda x: (x[1], x[0]))
    save_hxlated_output(
        outputs_configuration["orgs"],
        orgs,
        includes_header=False,
        includes_hxltags=False,
        output_dir=output_dir,
        today=today,
        num_orgs=len(orgs),
    )
    if not saveprefiltered:
        try:
            remove(prefiltered_path)
        except FileNotFoundError:
            pass
    try:
        remove(join(output_dir, dportal_filename))
    except FileNotFoundError:
        pass
