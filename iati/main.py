import logging
from os import remove
from os.path import join
from urllib.parse import quote

import diterator
from hdx.location.currency import Currency
from hdx.utilities.saver import save_hxlated_output

from . import checks
from .activity import Activity
from .calculatesplits import CalculateSplits
from .lookups import Lookups
from .smalldactivity import SmallDActivity

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
    filterdate,
    errors_on_exit,
):
    if filterdate:
        text = f"removing transactions before {filterdate}"
    else:
        text = "without removing transactions before a certain date"
    logger.info(f"Running {whattorun} {text}")
    Lookups.configuration = configuration
    Lookups.checks = checks[whattorun](errors_on_exit)
    Lookups.filter_transaction_date = filterdate
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
    dactivities = list()
    xmliterator = diterator.XMLIterator(dportal_path)
    number_query_activities = 0
    prefiltered_path = join(output_dir, "prefiltered.xml")
    with open(prefiltered_path, "w") as writer:
        writer.write(
            '<?xml version="1.0" encoding="UTF-8"?>\n<iati-activities version="2.03">\n'
        )
        for dactivity in xmliterator:
            number_query_activities += 1
            if number_query_activities % 1000 == 0:
                logger.info(f"Read {number_query_activities} activities")
            if Lookups.checks.exclude_dactivity(dactivity):
                continue
            Lookups.add_reporting_org(dactivity)
            dactivities.append(SmallDActivity(dactivity))
            writer.write(dactivity.node.toxml())
            del dactivity
        writer.write("\n</iati-activities>")
    del xmliterator  # Maybe this helps garbage collector?
    try:
        remove(join(output_dir, dportal_filename))
    except FileNotFoundError:
        pass
    logger.info(f"D-Portal returned {number_query_activities} activities")
    number_dactivities = len(dactivities)
    if number_dactivities == number_query_activities:
        logger.info(f"No prefiltering performed")
        try:
            remove(prefiltered_path)
        except FileNotFoundError:
            pass
    else:
        logger.info(f"Prefiltered to {number_dactivities} activities")
    #    Lookups.build_reporting_org_blocklist(dactivities)
    Lookups.add_participating_orgs(dactivities)

    # Build the accumulators from the IATI activities and transactions
    logger.info("Processing activities")
    flows = dict()
    transactions = list()
    all_skipped = 0
    for i, dactivity in enumerate(reversed(dactivities)):
        activity, skipped = Activity.get_activity(dactivity)
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
        num_skipped=all_skipped,
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
