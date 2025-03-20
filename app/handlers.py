from aiohttp import web
from pydantic import ValidationError

from services import ConverterService
from models import ConversionRequest
from log_setup import server_logger

converter_routes = web.RouteTableDef()


@converter_routes.post('/api/v1/convert')
async def convert(request: web.Request):
    """
    Endpoint to convert cryptocurrency.
    """
    data = await request.json()
    try:
        conversion_request = ConversionRequest(**data)
    except ValidationError as exc:
        return web.json_response({
            'status': 'error',
            'message': str(exc)
        }, status=400)

    conv_service = ConverterService()
    res = await conv_service.convert(conversion_request)

    server_logger.info(f'Received conversion request: {res}')

    return web.json_response({
        'status': 'success',
        'message': res.model_dump()
    })
