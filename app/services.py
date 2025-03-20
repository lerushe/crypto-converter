import asyncio
import datetime
from decimal import Decimal

import aiohttp

from log_setup import server_logger
from models import ExchangeService, ConversionRequest, ConversionResponse


class ConversionNotFound(Exception):
    pass


class ConverterService:

    def __init__(self):
        self.binance_url: str = 'https://api.binance.com/api/v3/ticker/price'
        self.kucoin_url: str = 'https://api.kucoin.com/api/v1/market/orderbook/level1'
        self.available_conversion_services = [ExchangeService.KUCOIN, ExchangeService.BINANCE]
        self.intermediary_currencies = ['BTC', 'USDT', 'ETH']

    async def _request(self, url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if not response.ok:
                    # TODO fix logger
                    server_logger.error(f'Conversion rate is not found, response: {await response.text()}')
                    return None
                data = await response.json()
                return data

    async def fetch_binance_rate(self, currency_from: str, currency_to: str) -> Decimal | None:
        data = await self._request(f'{self.binance_url}?symbol={currency_from}{currency_to}')
        server_logger.info(
            f'Request to Binance was proceeded, currency: {currency_from} - {currency_to}, result: {data}'
        )
        if data is None:
            return None
        return Decimal(data['price'])

    async def fetch_kucoin_rate(self, currency_from: str, currency_to: str) -> Decimal | None:
        data = await self._request(f'{self.kucoin_url}?symbol={currency_from}-{currency_to}')
        server_logger.info(
            f'Request to KuCoin was proceeded, currency: {currency_from} - {currency_to}, result: {data}'
        )
        if data is None:
            return None
        if not data['data']:
            return None
        return Decimal(data['data']['price'])

    async def fetch_rate_by_service(self, exchange_service: ExchangeService, currency_from: str, currency_to: str):
        match exchange_service:
            case ExchangeService.KUCOIN:
                return await self.fetch_kucoin_rate(currency_from, currency_to)
            case ExchangeService.BINANCE:
                return await self.fetch_binance_rate(currency_from, currency_to)
            case _:
                raise Exception(f'Provided Exchange service {exchange_service} is not supported')

    async def fetch_rate_by_intermediary_currency(
        self, currency_from: str, currency_to: str
    ) -> tuple[Decimal | None, ExchangeService | None]:
        conversion_services_to_fetch = set(self.available_conversion_services)
        currencies_to_fetch = set(self.intermediary_currencies) - {currency_from, currency_to}
        for exchange_service in conversion_services_to_fetch:
            for intermediate_currency in currencies_to_fetch:
                first_rate_request = self.fetch_rate_by_service(
                    exchange_service, currency_from, intermediate_currency
                )
                second_rate_request = self.fetch_rate_by_service(
                    exchange_service, intermediate_currency, currency_to
                )
                first_rate, second_rate = await asyncio.gather(first_rate_request, second_rate_request)
                if first_rate is not None and second_rate is not None:
                    return first_rate * second_rate, exchange_service

        return None, None

    @staticmethod
    async def make_conversion_response(
        exchange_service: ExchangeService, currency_from: str, currency_to: str, rate: Decimal, amount: Decimal
    ):
        return ConversionResponse(
            currency_from=currency_from,
            currency_to=currency_to,
            exchange=exchange_service,
            rate=rate,
            result=amount * rate,
            updated_at=int(datetime.datetime.now().timestamp())
        )

    async def convert(self, conversion_request: ConversionRequest) -> ConversionResponse:
        conversion_services_to_fetch = set(self.available_conversion_services)
        if conversion_request.exchange is not None:
            rate = await self.fetch_rate_by_service(
                conversion_request.exchange, conversion_request.currency_from, conversion_request.currency_to
            )
            server_logger.info(f'Attempt 1: {rate}')
            if rate is not None:
                return await self.make_conversion_response(
                    conversion_request.exchange, conversion_request.currency_from, conversion_request.currency_to, rate,
                    conversion_request.amount
                )
            conversion_services_to_fetch.remove(conversion_request.exchange)

        for exchange_service in conversion_services_to_fetch:
            rate = await self.fetch_rate_by_service(
                exchange_service, conversion_request.currency_from, conversion_request.currency_to
            )
            server_logger.info(f'Attempt 2: {rate}')
            if rate is not None:
                return await self.make_conversion_response(
                    conversion_request.exchange, conversion_request.currency_from, conversion_request.currency_to, rate,
                    conversion_request.amount
                )

        rate, exchange_service = await self.fetch_rate_by_intermediary_currency(
            conversion_request.currency_from, conversion_request.currency_to
        )
        if rate is not None:
            return await self.make_conversion_response(
                exchange_service, conversion_request.currency_from, conversion_request.currency_to, rate,
                conversion_request.amount
            )

        raise ConversionNotFound('No exchange services and conversion rates for specified request')



