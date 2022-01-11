from iati.climate_checks import ClimateChecks
from iati.covid_checks import CovidChecks
from iati.ebola_checks import EbolaChecks
from iati.southsudan_checks import SouthSudanChecks

checks = {
    "covid": CovidChecks,
    "ebola": EbolaChecks,
    "climate": ClimateChecks,
    "southsudan": SouthSudanChecks,
}
