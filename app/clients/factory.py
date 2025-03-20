from app.clients.base import ExchangeClient
from app.clients.binance import BinanceClient
from app.clients.kucoin import KuCoinClient
from app.models import ExchangeService


class ExchangeClientFactory:
    mapping = {
        ExchangeService.BINANCE: BinanceClient,
        ExchangeService.KUCOIN: KuCoinClient,
    }

    @classmethod
    def get_client(cls, name: ExchangeService) -> ExchangeClient:
        client_class = cls.mapping.get(name)
        if client_class is None:
            raise ValueError(f'Unsupported exchange service: {name}')
        return client_class()
