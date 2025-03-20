from decimal import Decimal

from app.clients.base import ExchangeClient
from app.log_setup import server_logger


class BinanceClient(ExchangeClient):
    base_url = 'https://api.binance.com'

    async def fetch_rate(self, currency_from: str, currency_to: str) -> Decimal | None:
        # Logic can be improved with fetching also {currency_to}{currency_from} and  converting it to needed rate
        data = await self._request(f'/api/v3/ticker/price?symbol={currency_from}{currency_to}')
        server_logger.info(
            f'Request to Binance was proceeded, currency: {currency_from} - {currency_to}, result: {data}'
        )
        if data is None or not data.get('price'):
            return None
        return Decimal(data['price'])
