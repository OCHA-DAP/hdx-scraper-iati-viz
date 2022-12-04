import iati.utilities as flatten


class SmallNarrativeText:
    __slots__ = ["defaulttext", "narratives"]

    def __init__(self, narrativetext):
        self.defaulttext = str(narrativetext)
        self.narratives = flatten.flatten(narrativetext.narratives)

    def __str__(self):
        return self.defaulttext
