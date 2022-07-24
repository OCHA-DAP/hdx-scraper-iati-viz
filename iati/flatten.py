from diterator.wrappers import CodedItem, NarrativeText, Organisation

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
