from unittest.mock import AsyncMock, patch

import pytest

from app.services import ConverterService


@pytest.fixture
def redis_mock():
    redis_client = AsyncMock()
    return redis_client


@pytest.fixture
def converter_service(redis_mock):
    with patch('app.clients.factory.ExchangeClientFactory.get_client') as get_client_mock:
        service = ConverterService(
            redis_client=redis_mock,
            redis_timeout=3600,
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
