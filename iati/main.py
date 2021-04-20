# -*- coding: utf-8 -*-
import logging
from urllib.parse import quote

from diterator import XMLIterator

logger = logging.getLogger(__name__)


def retrieve_activities(configuration, retriever, dportal_params):
    """
    Downloads activity data from D-Portal. Filters them and returns a
    list of activities.
    """
    dportal_configuration = configuration['dportal']
    url = dportal_configuration['url'] % quote(dportal_configuration['query'].format(dportal_params))
    filename = 'dportal.xml'
    dportal_path = retriever.retrieve_file(url, filename, 'D-Portal activities', False)
    return XMLIterator(dportal_path)


def start(configuration, retriever, outputs, tabs, dportal_params):
    def update_tab(name, data):
        logger.info('Updating tab: %s' % name)
        for output in outputs.values():
            output.update_tab(name, data)

    activity_totals = dict()
    activity_headers = [['Reporting org', 'Is strict?', 'Humanitarian only?', 'Activities'],
                        ['#org+reporting', '#meta+bool+strict', '#meta+bool+humanitarian', '#indicator+activities+num']]
    # if 'flows' in tabs:...
    # headers = [['Month', 'Reporting org', 'Sector', 'Country name', 'Country code', 'Is strict?', 'Humanitarian only?'],
    #            ['#date+month', '#org+reporting', '#sector', '#country+name', '#country+code', '#meta+bool+strict', '#meta+bool+humanitarian']]
    for activity in retrieve_activities(configuration, retriever, dportal_params):
        if activity.secondary_reporter:
            continue
        reporting_org = activity.reporting_org
        reporting_org_totals = activity_totals.get(reporting_org, dict())
        strict = is_strict(activity)
        strict_totals = reporting_org_totals.get(strict, dict())
        humanitarian = is_humanitarian(activity)
        total = strict_totals.get(humanitarian, 0)
        strict_totals[humanitarian] = total + 1
        reporting_org_totals[strict] = strict_totals
        activity_totals[reporting_org] = reporting_org_totals
