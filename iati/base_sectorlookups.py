class BaseSectorLookups:
    def __init__(self, retriever, configuration, sector_data="default"):
        self.default_sector = configuration["default_sector"]
        sector_info = retriever.download_json(configuration["sector_data"][sector_data])
        self.sector_info = sector_info

    def get_sector_group_name(self, code):
        """Look up a group name for a 3- or 5-digit sector code."""
        code = code[:3]
        if code in self.sector_info:
            return self.sector_info[code]["dac-group"]
        else:
            return self.default_sector
