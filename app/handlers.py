from aiohttp import web
from pydantic import ValidationError

from app.models import ConversionRequest
from app.services import ConversionNotFound, ConverterService

converter_routes = web.RouteTableDef()


@converter_routes.post('/api/v1/convert')
async def convert(request: web.Request):
    data = await request.json()
    try:
        conversion_request = ConversionRequest(**data)
        converter_service: ConverterService = request.app['converter_service']
        res = await converter_service.convert(conversion_request)
    except (ValidationError, ConversionNotFound) as exc:
        return web.json_response({
            'status': 'error',
            'message': str(exc)
        }, status=400)

    return web.json_response(res.model_dump(mode='json'))
