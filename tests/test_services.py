import time
from decimal import Decimal

import pytest

from app.models import ConversionRequest, ExchangeService
from app.services import ConversionNotFound


@pytest.mark.asyncio
async def test_direct_conversion_with_specific_exchange(converter_service, binance_client_mock):
    service, get_client_mock = converter_service
    get_client_mock.return_value = binance_client_mock
    binance_client_mock.fetch_rate.return_value = Decimal('3.14159')

    request = ConversionRequest(
        currency_from='BTC',
        currency_to='ETH',
        exchange=ExchangeService.BINANCE,
        amount=Decimal('1.0'),
        cache_max_seconds=None
    )

    response = await service.convert(request)

    get_client_mock.assert_called_with(ExchangeService.BINANCE)
    assert response.exchange == ExchangeService.BINANCE
    assert response.model_dump()['rate'] == '3.14'
    assert response.model_dump()['result'] == '3.14'


@pytest.mark.asyncio
async def test_dynamic_exchange_selection(converter_service, binance_client_mock, kucoin_client_mock):
    service, get_client_mock = converter_service

    def get_client_side_effect(exchange):
        if exchange == ExchangeService.BINANCE:
            binance_client_mock.fetch_rate.return_value = None
            return binance_client_mock
        elif exchange == ExchangeService.KUCOIN:
            kucoin_client_mock.fetch_rate.return_value = Decimal('2.71828')
            return kucoin_client_mock

    get_client_mock.side_effect = get_client_side_effect

    request = ConversionRequest(
        currency_from='ETH',
        currency_to='BTC',
        exchange=None,
        amount=Decimal('1.0'),
        cache_max_seconds=None
    )

    response = await service.convert(request)

    assert response.exchange == ExchangeService.KUCOIN
    assert response.model_dump()['rate'] == '2.72'


@pytest.mark.parametrize('cache_updated_delta, is_expired', [
        (60, False),
        (600, True),
])
@pytest.mark.asyncio
async def test_cache_conversion(converter_service, redis_mock, binance_client_mock, cache_updated_delta, is_expired):
    service, get_client_mock = converter_service

    cached_time = int(time.time()) - cache_updated_delta
    cached_data = {
        'rate': '1.23456',
        'updated_at': cached_time,
        'exchange_service': ExchangeService.BINANCE
    }
    redis_mock.hgetall.return_value = cached_data

    request = ConversionRequest(
        currency_from='BTC',
        currency_to='USDT',
        exchange='binance',
        amount=Decimal('2.0'),
        cache_max_seconds=300
    )
    get_client_mock.return_value = binance_client_mock
    binance_client_mock.fetch_rate.return_value = Decimal('1.23456')

    response = await service.convert(request)

    if is_expired:
        get_client_mock.assert_called()
        binance_client_mock.fetch_rate.assert_called()
    else:
        assert response.updated_at == cached_time
        get_client_mock.assert_not_called()

    assert response.exchange == ExchangeService.BINANCE
    assert response.model_dump()['rate'] == '1.23'
    assert response.model_dump()['result'] == '2.47'


@pytest.mark.asyncio
async def test_indirect_conversion_via_intermediary(converter_service, binance_client_mock):
    service, get_client_mock = converter_service
    get_client_mock.return_value = binance_client_mock

    binance_client_mock.fetch_rate.side_effect = lambda from_curr, to_curr: (
        None if (from_curr == 'TRX' and to_curr == 'ADA') else
        Decimal('0.5') if (from_curr == 'TRX' and to_curr == 'USDT') else
        Decimal('2.0') if (from_curr == 'USDT' and to_curr == 'ADA') else
        None
    )

    request = ConversionRequest(
        currency_from='TRX',
        currency_to='ADA',
        exchange=None,
        amount=Decimal('10.0'),
        cache_max_seconds=None
    )

    response = await service.convert(request)

    assert response.exchange == 'binance'
    assert response.model_dump()['rate'] == '1.00'
    assert response.model_dump()['result'] == '10.00'


@pytest.mark.asyncio
async def test_conversion_not_found(converter_service, binance_client_mock, kucoin_client_mock):
    service, get_client_mock = converter_service

    def get_client_side_effect(exchange):
        if exchange == ExchangeService.BINANCE:
            binance_client_mock.fetch_rate.return_value = None
            return binance_client_mock
        elif exchange == ExchangeService.KUCOIN:
            kucoin_client_mock.fetch_rate.return_value = None
            return kucoin_client_mock

    get_client_mock.side_effect = get_client_side_effect

    request = ConversionRequest(
        currency_from='UNKNOWN1',
        currency_to='UNKNOWN2',
        exchange=None,
        amount=Decimal('1.0'),
        cache_max_seconds=None
    )

    with pytest.raises(ConversionNotFound):
        await service.convert(request)
