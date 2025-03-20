import urllib.parse
from abc import ABC, abstractmethod
from decimal import Decimal

from aiohttp import ClientSession

from app.log_setup import server_logger


class ExchangeClient(ABC):
    base_url: str = ''

    async def _request(self, path):
        url = urllib.parse.urljoin(self.base_url, path)
        async with ClientSession() as session:
            async with session.get(url) as response:
                if not response.ok:
                    server_logger.error(f'Conversion rate is not found, response: {response.status} {response.reason}')
                    return None
                data = await response.json()
                return data

    @abstractmethod
    async def fetch_rate(self, currency_from: str, currency_to: str) -> Decimal | None:
        pass
