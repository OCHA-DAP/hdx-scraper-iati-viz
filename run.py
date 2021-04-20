# -*- coding: utf-8 -*-
import argparse
import logging
from datetime import datetime
from os import getenv
from os.path import join

from hdx.facades.keyword_arguments import facade
from hdx.hdx_configuration import Configuration
from hdx.scraper.exceloutput import ExcelOutput
from hdx.scraper.googlesheets import GoogleSheets
from hdx.scraper.jsonoutput import JsonOutput
from hdx.scraper.nooutput import NoOutput
from hdx.utilities.downloader import Download
from hdx.utilities.easy_logging import setup_logging
from hdx.utilities.path import temp_dir
from hdx.utilities.retriever import Retrieve

from iati.main import start

setup_logging()
logger = logging.getLogger()


VERSION = 1.0


def parse_args():
    parser = argparse.ArgumentParser(description='Covid IATI Explorer')
    parser.add_argument('-ua', '--user_agent', default=None, help='user agent')
    parser.add_argument('-pp', '--preprefix', default=None, help='preprefix')
    parser.add_argument('-hs', '--hdx_site', default=None, help='HDX site to use')
    parser.add_argument('-xl', '--excel_path', default=None, help='Path for Excel output')
    parser.add_argument('-gs', '--gsheet_auth', default=None, help='Credentials for accessing Google Sheets')
    parser.add_argument('-us', '--updatespreadsheets', default=None, help='Spreadsheets to update')
    parser.add_argument('-ut', '--updatetabs', default=None, help='Sheets to update')
    parser.add_argument('-nj', '--nojson', default=False, action='store_true', help='Do not update json')
    parser.add_argument('-sd', '--saved_dir', default='saved_data', help='Saved data folder')
    parser.add_argument('-sv', '--save', default=False, action='store_true', help='Save downloaded data')
    parser.add_argument('-us', '--use_saved', default=False, action='store_true', help='Use saved data')
    parser.add_argument('-dp', '--dportal_params', default='', help='Parameters for DPortal query (eg. limit X, offset Y')
    args = parser.parse_args()
    return args


def main(excel_path, gsheet_auth, updatesheets, updatetabs, nojson, saved_dir, save, use_saved, dportal_params, **ignore):
    logger.info('##### hdx-scraper-iati-viz version %.1f ####' % VERSION)
    configuration = Configuration.read()
    with temp_dir() as temp_folder:
        with Download(user_agent='HDX-IATI-COVID19') as downloader:
            retriever = Retrieve(downloader, configuration['fallback_dir'], saved_dir, temp_folder, save, use_saved)
            updatesheets = args.updatespreadsheets
            if updatesheets is None:
                updatesheets = getenv('UPDATESHEETS')
            if updatesheets:
                updatesheets = updatesheets.split(',')
            else:
                updatesheets = None
            tabs = configuration['tabs']
            if updatetabs is None:
                updatetabs = list(tabs.keys())
                logger.info('Updating all tabs')
            else:
                logger.info('Updating only these tabs: %s' % updatetabs)
            noout = NoOutput(updatetabs)
            if excel_path:
                excelout = ExcelOutput(excel_path, tabs, updatetabs)
            else:
                excelout = noout
            if gsheet_auth:
                gsheets = GoogleSheets(configuration, gsheet_auth, updatesheets, tabs, updatetabs)
            else:
                gsheets = noout
            if nojson:
                jsonout = noout
            else:
                jsonout = JsonOutput(configuration, updatetabs)
            outputs = {'gsheets': gsheets, 'excel': excelout, 'json': jsonout}
            start(configuration, downloader, outputs, updatetabs, dportal_params)
            jsonout.save()
            excelout.save()


if __name__ == '__main__':
    args = parse_args()
    user_agent = args.user_agent
    if user_agent is None:
        user_agent = getenv('USER_AGENT')
        if user_agent is None:
            user_agent = 'test'
    preprefix = args.preprefix
    if preprefix is None:
        preprefix = getenv('PREPREFIX')
    hdx_site = args.hdx_site
    if hdx_site is None:
        hdx_site = getenv('HDX_SITE', 'prod')
    gsheet_auth = args.gsheet_auth
    if gsheet_auth is None:
        gsheet_auth = getenv('GSHEET_AUTH')
    updatesheets = args.updatespreadsheets
    if updatesheets is None:
        updatesheets = getenv('UPDATESHEETS')
    if updatesheets:
        updatesheets = updatesheets.split(',')
    else:
        updatesheets = None
    if args.updatetabs:
        updatetabs = args.updatetabs.split(',')
    else:
        updatetabs = None
    facade(main, hdx_read_only=True, user_agent=user_agent, preprefix=preprefix, hdx_site=hdx_site,
           project_config_yaml=join('config', 'project_configuration.yml'), excel_path=args.excel_path,
           gsheet_auth=gsheet_auth, updatesheets=updatesheets, updatetabs=updatetabs, nojson=args.nojson,
           saved_dir=args.saved_dir, save=args.save, use_saved=args.use_saved, dportal_params=args.dportal_params)
