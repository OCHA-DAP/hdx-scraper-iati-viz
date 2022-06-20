from iati.climate_checks import ClimateChecks
from iati.covid_checks import CovidChecks
from iati.ebola_checks import EbolaChecks
from iati.glide_checks import GlideChecks
from iati.hrp_checks import HRPChecks
from iati.southsudan_checks import SouthSudanChecks
from iati.ukraine_checks import UkraineChecks

checks = {
    "covid": CovidChecks,
    "ebola": EbolaChecks,
    "climate": ClimateChecks,
    "southsudan": SouthSudanChecks,
    "ukraine": UkraineChecks,
    "hrp": HRPChecks,
    "glide": GlideChecks,
}
