# -*- coding: utf-8 -*-
import logging
from urllib.parse import quote

from diterator import XMLIterator

from iati.activities import Activities
from iati.utils import unpack_key

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


def should_ignore_activity(activity):
    return False


#
# Postprocessing
#

def postprocess_accumulators (accumulators):
    """ Unpack the accumulators into a usable data structure """
    rows = []
    for key in sorted(accumulators.keys()):
        value = accumulators[key]
        parts = unpack_key(key)
        parts["net"] = accumulators[key]["net"]
        parts["total"] = accumulators[key]["total"]
        rows.append(parts)
    return rows

def postprocess_activity_counts (activity_counts):
    result = {}
    for key in activity_counts.keys():
        result[key] = []
        for entry in sorted(activity_counts[key].keys()):
            result[key].append({
                key: entry[0],
                "is_humanitarian": entry[1],
                "is_strict": entry[2],
                "activities": len(activity_counts[key][entry]),
            })
    return result


def start(configuration, retriever, outputs, tabs, dportal_params):
    def update_tab(name, data):
        logger.info('Updating tab: %s' % name)
        for output in outputs.values():
            output.update_tab(name, data)

    activities = Activities()
    for no_activities, activity in enumerate(retrieve_activities(configuration, retriever, dportal_params)):
        if should_ignore_activity(activity):
            continue
        activities.process_activity(activity)
    logger.info(f'Processed {no_activities} activities')
    commitments_spending = postprocess_accumulators(activities.accumulators)
    activity_counts = postprocess_activity_counts(activities.activity_counts)
    update_tab('commitmentsspending', commitments_spending)
    update_tab('activitytotals', activity_counts)
