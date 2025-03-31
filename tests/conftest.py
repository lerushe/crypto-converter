from unittest.mock import AsyncMock, patch

import pytest

from app.cache import RateCache
from app.services import ConverterService


@pytest.fixture
def redis_mock():
    redis_client = AsyncMock()
    return redis_client


@pytest.fixture
def cache_mock(redis_mock):
    return RateCache(redis_client = redis_mock, redis_timeout = 3600)


@pytest.fixture
def converter_service(cache_mock):
    with patch('app.clients.factory.ExchangeClientFactory.get_client') as get_client_mock:
        service = ConverterService(
            cache_client=cache_mock,
            intermediary_currencies=['USDT', 'BTC', 'ETH']
        )
        yield service, get_client_mock


@pytest.fixture
def binance_client_mock():
    client = AsyncMock()
    return client


@pytest.fixture
def kucoin_client_mock():
    client = AsyncMock()
    return client
