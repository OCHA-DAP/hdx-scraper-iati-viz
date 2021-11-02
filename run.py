import argparse
import logging
from datetime import datetime
from os import getenv, mkdir
from os.path import join
from shutil import rmtree

from hdx.facades.keyword_arguments import facade
from hdx.hdx_configuration import Configuration
from hdx.utilities.downloader import Download
from hdx.utilities.easy_logging import setup_logging
from hdx.utilities.retriever import Retrieve
from iati.data import download_all
from iati.main import start

setup_logging()
logger = logging.getLogger()


VERSION = 4.0


def parse_args():
    parser = argparse.ArgumentParser(description="Covid IATI Explorer")
    parser.add_argument(
        "-ac", "--action", default=None, help="action (download or run)"
    )
    parser.add_argument("-ua", "--user_agent", default=None, help="user agent")
    parser.add_argument("-pp", "--preprefix", default=None, help="preprefix")
    parser.add_argument("-hs", "--hdx_site", default=None, help="HDX site to use")
    parser.add_argument("-od", "--output_dir", default="output", help="Output folder")
    parser.add_argument(
        "-sd", "--saved_dir", default="saved_data", help="Saved data folder"
    )
    parser.add_argument(
        "-dp",
        "--dportal_params",
        default="",
        help="Parameters for DPortal query (eg. limit X, offset Y",
    )
    parser.add_argument(
        "-wh", "--what", default="covid", help="What to run eg. covid, ebola"
    )
    parser.add_argument(
        "-df", "--date_filter", default="2020-01", help="Start date of date filter"
    )
    args = parser.parse_args()
    return args


def main(
    action,
    output_dir,
    saved_dir,
    dportal_params,
    whattorun,
    filterdate,
    **ignore,
):
    logger.info(f"##### hdx-scraper-iati-viz version {VERSION:.1f} ####")
    configuration = Configuration.read()
    data_dir = f"{saved_dir}_{whattorun}"
    if action == "download":
        download_all(configuration, data_dir, dportal_params, whattorun)
    else:
        output_dir = f"{output_dir}_{whattorun}"
        rmtree(output_dir, ignore_errors=True)
        mkdir(output_dir)
        today = datetime.utcnow().isoformat()
        start(
            configuration,
            today,
            output_dir,
            data_dir,
            whattorun,
            filterdate,
        )


if __name__ == "__main__":
    args = parse_args()
    user_agent = args.user_agent
    if user_agent is None:
        user_agent = getenv("USER_AGENT")
        if user_agent is None:
            user_agent = "hdx-scraper-iati-viz"
    preprefix = args.preprefix
    if preprefix is None:
        preprefix = getenv("PREPREFIX")
    hdx_site = args.hdx_site
    if hdx_site is None:
        hdx_site = getenv("HDX_SITE", "prod")
    facade(
        main,
        hdx_read_only=True,
        user_agent=user_agent,
        preprefix=preprefix,
        hdx_site=hdx_site,
        project_config_yaml=join("config", "project_configuration.yml"),
        action=args.action,
        output_dir=args.output_dir,
        saved_dir=args.saved_dir,
        dportal_params=args.dportal_params,
        whattorun=args.what,
        filterdate=args.date_filter,
    )
