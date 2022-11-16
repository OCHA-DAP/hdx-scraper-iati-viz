from iati import BaseSectorLookups


class FoodSecuritySectorLookups(BaseSectorLookups):
    def __init__(self, retriever, configuration):
        super().__init__(retriever, configuration, sector_data="foodsecurity")
        sector_info = self.sector_info
        self.sector_info = dict()
        for info in sector_info["data"]:
            self.sector_info[info["code"]] = info["name"]

    def get_sector_group_name(self, code):
        """Look up a group name for a 5-digit sector code."""
        if code in self.sector_info:
            return self.sector_info[code]
        else:
            return self.default_sector
