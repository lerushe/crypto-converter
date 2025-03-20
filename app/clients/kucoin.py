from decimal import Decimal

from app.clients.base import ExchangeClient
from app.log_setup import server_logger


class KuCoinClient(ExchangeClient):
    base_url = 'https://api.kucoin.com'

    async def fetch_rate(self, currency_from: str, currency_to: str) -> Decimal | None:
        data = await self._request(f'/api/v1/market/orderbook/level1?symbol={currency_from}-{currency_to}')
        server_logger.info(
            f'Request to KuCoin was proceeded, currency: {currency_from} - {currency_to}, result: {data}'
        )
        if data is None or not data.get('data') or not data['data']['price']:
            return None
        return Decimal(data['data']['price'])
