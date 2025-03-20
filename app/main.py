import asyncio
import os

import redis.asyncio as redis
import uvloop
from aiohttp import web
from dotenv import load_dotenv

from app.handlers import converter_routes
from app.log_setup import init_logging
from app.services import ConverterService

load_dotenv()

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def create_redis_pool(app):
    app['redis'] = await redis.from_url(
        os.getenv('REDIS_URL', 'redis://redis:6379'),
        decode_responses=True,
        max_connections=10 
    )
    return app['redis']


async def init_converter_service(app):
    redis_timeout = int(os.getenv('REDIS_DEFAULT_TIMEOUT', 86400))
    intermediary_currencies = os.getenv('INTERMEDIARY_CURRENCIES', 'BTC,USDT,ETH').split(',')
    app['converter_service'] = ConverterService(
        app['redis'], redis_timeout=redis_timeout, intermediary_currencies=intermediary_currencies
    )


async def close_redis_pool(app):
    await app['redis'].close()


async def create_app():
    app = web.Application()
    app.add_routes(converter_routes)
    init_logging()
    app.on_startup.extend([create_redis_pool, init_converter_service])
    app.on_shutdown.append(close_redis_pool)
    return app


if __name__ == '__main__':
    web.run_app(create_app(), host='0.0.0.0', port=8080)
