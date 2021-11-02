import glob
import json
import logging
from os.path import join
from urllib.parse import quote

import diterator
import unicodecsv
from hdx.location.currency import Currency
from hdx.utilities.downloader import Download
from hdx.utilities.retriever import Retrieve
from natsort import natsorted


logger = logging.getLogger(__name__)


def is_xml(path):
    with open(path) as unknown_file:
        character = unknown_file.read(1)
        if character == "<":
            return True
    return False


def retrieve_dportal(configuration, retriever, dportal_params, whattorun):
    """
    Downloads activity data from D-Portal. Filters them and returns a
    list of activities.
    """
    dportal_configuration = configuration["dportal"]
    base_filename = dportal_configuration["filename"]
    dportal_limit = dportal_configuration["limit"]
    n = 0
    dont_exit = True
    while dont_exit:
        if dportal_params:
            params = dportal_params
            dont_exit = False
        else:
            offset = n * dportal_limit
            params = f"LIMIT {dportal_limit} OFFSET {offset}"
            logger.info(f"OFFSET {offset}")
        url = dportal_configuration["url"] % quote(
            dportal_configuration[f"{whattorun}_query"].format(params)
        )
        filename = base_filename.format(n)
        path = retriever.retrieve_file(url, filename, "D-Portal activities", False)
        if is_xml(path):
            n += 1
        else:
            # If the result isn't XML, we're done
            dont_exit = False


def download_all(configuration, data_dir, dportal_params, whattorun, downloader=None):
    retriever = Retrieve(
        downloader or Download(),
        configuration["fallback_dir"],
        data_dir,
        data_dir,
        True,
        False,
    )
    Currency.setup(
        retriever=retriever,
        fallback_historic_to_current=True,
        fallback_current_to_static=True,
    )
    retrieve_dportal(configuration, retriever, dportal_params, whattorun)


def dactivity_iterator(data_dir, go_backwards=False):
    files = natsorted(glob.glob(join(data_dir, "dportal_*.xml")))
    if go_backwards:
        files = reversed(files)
    for file in files:
        if is_xml(file):
            logger.info(f"Reading {file}")
            xmliterator = diterator.XMLIterator(file)
            if go_backwards:
                xmliterator = reversed(list(xmliterator))
            for dactivity in xmliterator:
                yield dactivity
                del dactivity
            del xmliterator  # Maybe this helps garbage collector?


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