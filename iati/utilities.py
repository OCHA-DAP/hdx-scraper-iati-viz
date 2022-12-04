from dateutil.parser import ParserError
from diterator.wrappers import CodedItem, NarrativeText, Organisation
from hdx.utilities.dateparse import parse_date

from .smallnarrativetext import SmallNarrativeText


def flatten(obj):
    if isinstance(obj, list):
        return [flatten(x) for x in obj]
    elif isinstance(obj, dict):
        return {k: flatten(v) for k, v in obj.items()}
    elif isinstance(obj, NarrativeText):
        return SmallNarrativeText(obj)
    elif isinstance(obj, CodedItem):
        return type(
            "",
            (object,),
            {
                "code": obj.code,
                "type": obj.type,
                "vocabulary": obj.vocabulary,
                "percentage": obj.percentage,
            },
        )()
    elif isinstance(obj, Organisation):
        return type(
            "",
            (object,),
            {
                "name": flatten(obj.name),
                "ref": obj.ref,
                "role": obj.role,
                "type": obj.type,
            },
        )()
    else:
        return obj


def get_date_with_fallback(date1, date2):
    output_date = date1
    if output_date:
        try:
            output_date = parse_date(output_date)
        except ParserError:
            output_date = None
    if not output_date:
        output_date = date2
        if output_date:
            try:
                output_date = parse_date(output_date)
            except ParserError:
                output_date = None
        else:
            output_date = None
    return output_date
