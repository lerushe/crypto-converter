import time
from decimal import Decimal

import redis.asyncio as redis

from app.models import ExchangeService


class RateCache:
    def __init__(self, redis_client: redis.Redis, redis_timeout: int):
        self.redis_client = redis_client
        self.redis_default_timeout = redis_timeout
        self.cache_key_template = 'conversion:{currency_from}:{currency_to}'

    async def save_cache_rate(
        self, exchange_service: ExchangeService, currency_from: str, currency_to: str, rate: Decimal, updated_at: int
    ) -> None:
        cache_key = self.cache_key_template.format(currency_from=currency_from, currency_to=currency_to)
        await self.redis_client.hset(cache_key, mapping={
            'rate': str(rate),
            'updated_at': updated_at,
            'exchange_service': exchange_service
        })
        await self.redis_client.expire(cache_key, self.redis_default_timeout)

    async def load_cache_rate(
        self, currency_from: str, currency_to: str, cache_max_seconds: int
    ) -> tuple[Decimal | None, ExchangeService | None, int | None]:
        cache_key = self.cache_key_template.format(currency_from=currency_from, currency_to=currency_to)
        cached_data = await self.redis_client.hgetall(cache_key)
        if not cached_data:
            return None, None, None

        current_time = int(time.time())
        cache_updated_at = int(cached_data['updated_at'])
        if current_time - cache_updated_at > cache_max_seconds:
            return None, None, None

        return Decimal(cached_data['rate']), cached_data['exchange_service'], cache_updated_at
