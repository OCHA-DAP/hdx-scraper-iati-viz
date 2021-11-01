import logging
from os import remove
from urllib.parse import quote

from hdx.location.currency import Currency
from hdx.utilities.downloader import Download
from hdx.utilities.retriever import Retrieve

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
