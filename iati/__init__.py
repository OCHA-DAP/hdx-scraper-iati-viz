from .climate_checks import ClimateChecks
from .covid_checks import CovidChecks
from .ebola_checks import EbolaChecks
from .foodsecurity_checks import FoodSecurityChecks
from .southsudan_checks import SouthSudanChecks
from .ukraine_checks import UkraineChecks

checks = {
    "covid": CovidChecks,
    "ebola": EbolaChecks,
    "climate": ClimateChecks,
    "southsudan": SouthSudanChecks,
    "ukraine": UkraineChecks,
    "foodsecurity": FoodSecurityChecks,
}
