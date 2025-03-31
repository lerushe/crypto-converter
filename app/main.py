import asyncio
import os

import redis.asyncio as redis
import uvloop
from aiohttp import web
from dotenv import load_dotenv

from app.cache import RateCache
from app.handlers import converter_routes
from app.log_setup import init_logging
from app.services import ConverterService

load_dotenv()

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def init_cache_client(app):
    app['redis'] = await redis.from_url(
        os.getenv('REDIS_URL', 'redis://redis:6379'),
        decode_responses=True,
        max_connections=10
    )
    redis_timeout = int(os.getenv('REDIS_DEFAULT_TIMEOUT', 86400))
    app['rate_cache_client'] = RateCache(app['redis'], redis_timeout)


async def init_converter_service(app):
    intermediary_currencies = os.getenv('INTERMEDIARY_CURRENCIES', 'BTC,USDT,ETH').split(',')
    app['converter_service'] = ConverterService(
        app['rate_cache_client'], intermediary_currencies=intermediary_currencies
    )


async def close_redis_pool(app):
    await app['redis'].close()


async def create_app():
    app = web.Application()
    app.add_routes(converter_routes)
    init_logging()
    app.on_startup.extend([init_cache_client, init_converter_service])
    app.on_shutdown.append(close_redis_pool)
    return app


if __name__ == '__main__':
    web.run_app(create_app(), host='0.0.0.0', port=8080)
