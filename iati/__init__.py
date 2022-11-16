from .base_sectorlookups import BaseSectorLookups
from .climate_checks import ClimateChecks
from .covid_checks import CovidChecks
from .ebola_checks import EbolaChecks
from .foodsecurity_checks import FoodSecurityChecks
from .foodsecurity_sectorlookups import FoodSecuritySectorLookups
from .southsudan_checks import SouthSudanChecks
from .ukraine_checks import UkraineChecks

sector_lookups = {
    "covid": BaseSectorLookups,
    "ebola": BaseSectorLookups,
    "climate": BaseSectorLookups,
    "southsudan": BaseSectorLookups,
    "ukraine": BaseSectorLookups,
    "foodsecurity": FoodSecuritySectorLookups,
}

checks = {
    "covid": CovidChecks,
    "ebola": EbolaChecks,
    "climate": ClimateChecks,
    "southsudan": SouthSudanChecks,
    "ukraine": UkraineChecks,
    "foodsecurity": FoodSecurityChecks,
}
