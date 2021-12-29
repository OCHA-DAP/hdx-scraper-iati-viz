from iati.climate_checks import ClimateChecks
from iati.covid_checks import CovidChecks
from iati.ebola_checks import EbolaChecks

checks = {"covid": CovidChecks, "ebola": EbolaChecks, "climate": ClimateChecks}
