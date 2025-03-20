import asyncio

import uvloop
from aiohttp import web

from handlers import converter_routes
from log_setup import init_logging

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())


async def create_app():
    app = web.Application()
    app.add_routes(converter_routes)
    init_logging()
    return app


if __name__ == '__main__':
    web.run_app(create_app(), host='0.0.0.0', port=8080)
