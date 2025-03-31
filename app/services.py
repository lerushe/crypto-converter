import asyncio
import time
from decimal import Decimal

import redis.asyncio as redis

from app.clients.factory import ExchangeClientFactory
from app.log_setup import server_logger
from app.models import ConversionRequest, ConversionResponse, ExchangeService


class ConversionNotFound(Exception):
    pass


class ConverterService:

    def __init__(self, redis_client: redis.Redis, redis_timeout: int, intermediary_currencies: list[str]):
        self.redis_client = redis_client
        self.intermediary_currencies = intermediary_currencies
        self.redis_default_timeout = redis_timeout
        self.available_conversion_services = ExchangeClientFactory.mapping
        self.cache_key_template = 'conversion:{currency_from}:{currency_to}'

    async def _fetch_rate_by_intermediary_currency(
        self, currency_from: str, currency_to: str
    ) -> tuple[Decimal | None, ExchangeService | None]:
        server_logger.info('Trying to find exchange rate via intermediary currency')

        conversion_services_to_fetch = self.available_conversion_services
        currencies_to_fetch = set(self.intermediary_currencies) - {currency_from, currency_to}
        if not currencies_to_fetch:
            server_logger.info('Can not find any intermediary currency')
            return None, None

        for exchange_service in conversion_services_to_fetch:
            for intermediate_currency in currencies_to_fetch:
                client = ExchangeClientFactory.get_client(exchange_service)
                first_rate_request = client.fetch_rate(currency_from, intermediate_currency)
                second_rate_request = client.fetch_rate(intermediate_currency, currency_to)
                first_rate, second_rate = await asyncio.gather(first_rate_request, second_rate_request)
                if first_rate is not None and second_rate is not None:
                    return first_rate * second_rate, exchange_service

        return None, None

    async def _get_cache_rate(
        self, conversion_request: ConversionRequest
    ) -> tuple[Decimal | None, ExchangeService | None, int | None]:
        cache_key = self.cache_key_template.format(
            currency_from=conversion_request.currency_from, currency_to=conversion_request.currency_to
        )
        cached_data = await self.redis_client.hgetall(cache_key)
        if not cached_data:
            return None, None, None

        current_time = int(time.time())
        cache_updated_at = int(cached_data['updated_at'])
        if current_time - cache_updated_at > conversion_request.cache_max_seconds:
            return None, None, None
        server_logger.info(f'Using cached conversion rate: {cached_data}')
        return Decimal(cached_data['rate']), cached_data['exchange_service'], cache_updated_at

    async def _save_cache_rate(
        self, exchange_service: ExchangeService, currency_from: str, currency_to: str, rate: Decimal, updated_at: int
    ) -> None:
        cache_key = self.cache_key_template.format(currency_from=currency_from, currency_to=currency_to)
        await self.redis_client.hset(cache_key, mapping={
            'rate': str(rate),
            'updated_at': updated_at,
            'exchange_service': exchange_service
        })
        # Add expire timeout just to not have too old data
        await self.redis_client.expire(cache_key, self.redis_default_timeout)

    async def _prepare_conversion_response(
        self, exchange_service: ExchangeService, currency_from: str, currency_to: str, rate: Decimal,
        amount: Decimal, *, cache_updated_at: int | None = None
    ) -> ConversionResponse:
        updated_at = int(time.time())
        if cache_updated_at is None:
            await self._save_cache_rate(exchange_service, currency_from, currency_to, rate, updated_at)

        return ConversionResponse(
            currency_from=currency_from,
            currency_to=currency_to,
            exchange=exchange_service,
            rate=rate,
            result=amount * rate,
            updated_at=cache_updated_at or updated_at
        )

    async def convert(self, conversion_request: ConversionRequest) -> ConversionResponse:
        if conversion_request.cache_max_seconds is not None:
            rate, exchange_service, updated_at = await self._get_cache_rate(conversion_request)
            if rate is not None:
                return await self._prepare_conversion_response(
                    exchange_service, conversion_request.currency_from, conversion_request.currency_to, rate,
                    conversion_request.amount, cache_updated_at=updated_at
                )

        conversion_services_to_fetch = set(self.available_conversion_services)
        if conversion_request.exchange is not None:
            client = ExchangeClientFactory.get_client(conversion_request.exchange)
            rate = await client.fetch_rate(conversion_request.currency_from, conversion_request.currency_to)
            if rate is not None:
                return await self._prepare_conversion_response(
                    conversion_request.exchange, conversion_request.currency_from, conversion_request.currency_to, rate,
                    conversion_request.amount
                )
            conversion_services_to_fetch.remove(conversion_request.exchange)

        for exchange_service in conversion_services_to_fetch:
            client = ExchangeClientFactory.get_client(exchange_service)
            rate = await client.fetch_rate(conversion_request.currency_from, conversion_request.currency_to)
            if rate is not None:
                return await self._prepare_conversion_response(
                    exchange_service, conversion_request.currency_from, conversion_request.currency_to, rate,
                    conversion_request.amount
                )

        rate, exchange_service = await self._fetch_rate_by_intermediary_currency(
            conversion_request.currency_from, conversion_request.currency_to
        )
        if rate is not None:
            return await self._prepare_conversion_response(
                exchange_service, conversion_request.currency_from, conversion_request.currency_to, rate,
                conversion_request.amount
            )

        raise ConversionNotFound('No exchange services and conversion rates found for specified request')
