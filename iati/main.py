import json
import logging
from os import remove
from os.path import join
from urllib.parse import quote

import diterator
import unicodecsv
from hdx.location.currency import Currency

from . import checks
from .activity import Activity
from .calculatesplits import CalculateSplits
from .lookups import Lookups

logger = logging.getLogger(__name__)


def retrieve_dportal(configuration, retriever, whattorun, dportal_params=""):
    """
    Downloads activity data from D-Portal. Filters them and returns a
    list of activities.
    """
    dportal_configuration = configuration["dportal"]
    filename = dportal_configuration["filename"]
    url = dportal_configuration["url"] % quote(
        dportal_configuration[f"{whattorun}_query"].format(dportal_params)
    )
    return filename, retriever.retrieve_file(
        url, filename, "D-Portal activities", False
    )


def write(today, output_dir, configuration, configuration_key, rows, skipped=None):
    logger.info(f"Writing {configuration_key} files to {output_dir}")
    file_configuration = configuration[configuration_key]
    headers = file_configuration["headers"]
    hxltags = file_configuration["hxltags"]
    process_cols = file_configuration.get("process_cols", dict())
    csv_configuration = file_configuration["csv"]
    json_configuration = file_configuration["json"]
    csv_hxltags = csv_configuration.get("hxltags", hxltags)
    json_hxltags = json_configuration.get("hxltags", hxltags)
    hxltag_to_header = dict(zip(hxltags, headers))
    csv_headers = [hxltag_to_header[hxltag] for hxltag in csv_hxltags]
    metadata = {"#date+run": today, f"#meta+{configuration_key}+num": len(rows)}
    if skipped is not None:
        metadata[f"#meta+{configuration_key}+skipped+num"] = skipped
    metadata_json = json.dumps(metadata, indent=None, separators=(",", ":"))
    with open(join(output_dir, csv_configuration["filename"]), "wb") as output_csv:
        writer = unicodecsv.writer(output_csv, encoding="utf-8", lineterminator="\n")
        writer.writerow(csv_headers)
        writer.writerow(csv_hxltags)
        with open(join(output_dir, json_configuration["filename"]), "w") as output_json:
            output_json.write(f'{{"metadata":{metadata_json},"data":[\n')

            def write_row(inrow, ending):
                def get_outrow(file_hxltags):
                    outrow = dict()
                    for file_hxltag in file_hxltags:
                        expression = process_cols.get(file_hxltag)
                        if expression:
                            for i, hxltag in enumerate(hxltags):
                                expression = expression.replace(hxltag, f"inrow[{i}]")
                            outrow[file_hxltag] = eval(expression)
                        else:
                            outrow[file_hxltag] = inrow[hxltags.index(file_hxltag)]
                    return outrow

                writer.writerow(get_outrow(csv_hxltags).values())
                row = get_outrow(json_hxltags)
                output_json.write(
                    json.dumps(row, indent=None, separators=(",", ":")) + ending
                )

            [write_row(row, ",\n") for row in rows[:-1]]
            write_row(rows[-1], "]")
            output_json.write("}")


def start(
    configuration, today, retriever, output_dir, dportal_params, whattorun, filterdate
):
    if filterdate:
        text = f"removing transactions before {filterdate}"
    else:
        text = "without removing transactions before a certain date"
    logger.info(f"Running {whattorun} {text}")
    Lookups.checks = checks[whattorun]
    Lookups.filter_transaction_date = filterdate
    dportal_filename, dportal_path = retrieve_dportal(
        configuration, retriever, whattorun, dportal_params
    )
    Lookups.setup(configuration["lookups"])
    Currency.setup(
        retriever=retriever,
        fallback_historic_to_current=True,
        fallback_current_to_static=True,
    )
    CalculateSplits.setup(configuration["calculate_splits"])

    # Build org name lookup
    dactivities = list()
    xmliterator = diterator.XMLIterator(dportal_path)
    for dactivity in xmliterator:
        Lookups.add_reporting_org(dactivity)
        dactivities.append(dactivity)
    del xmliterator  # Maybe this helps garbage collector?
    #    Lookups.build_reporting_org_blocklist(dactivities)
    Lookups.add_participating_orgs(dactivities)

    # Build the accumulators from the IATI activities and transactions
    flows = dict()
    transactions = list()
    all_skipped = 0
    for i, dactivity in enumerate(reversed(dactivities)):
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
    try:
        remove(join(output_dir, dportal_filename))
    except FileNotFoundError:
        pass
