# -*- coding: utf-8 -*-
from iati.covid_checks import CovidChecks
from iati.ebola_checks import EbolaChecks

checks = {'covid': CovidChecks, 'ebola': EbolaChecks, 'use': None}