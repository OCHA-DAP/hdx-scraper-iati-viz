# -*- coding: utf-8 -*-
import logging

import exchangerates

logger = logging.getLogger(__name__)

EXCHANGE_RATES_URL = "https://codeforiati.org/exchangerates-scraper/consolidated.csv"

FALLBACK_RATES_URL = "https://api.exchangerate.host/latest?base=usd"


class FXRates:
    def __init__(self, configuration, retriever):
        logger.info('Reading in exchange rates data')
        rates_path = retriever.retrieve_file(configuration['rates_url'], 'rates.csv', 'exchange rates', True)
        rjson = retriever.retrieve_json(configuration['fallback_rates_url'], 'fallbackrates.json',
                                        'fallback exchange rates', True)
        fallback_rates = rjson['rates']

        self.fx_rates = exchangerates.CurrencyConverter(update=False, source=rates_path)
        self.fallback_rates = fallback_rates

    def get_value_usd(self, date, currency, value):
        try:
            fx_rate = self.fx_rates.closest_rate(currency, date).get('conversion_rate')
        except exchangerates.UnknownCurrencyException:
            fx_rate = self.fallback_rates.get(currency)
            if fx_rate is None:
                logger.exception(f'Currency {currency} is invalid!')
                return 0
        return value / fx_rate
