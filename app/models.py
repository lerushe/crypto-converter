from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, field_serializer


class ExchangeService(str, Enum):
    BINANCE = 'binance'
    KUCOIN = 'kucoin'


class ConversionRequest(BaseModel):
    currency_from: str
    currency_to: str
    exchange: ExchangeService | None = None
    amount: Decimal
    cache_max_seconds: int | None = None


class ConversionResponse(BaseModel):
    currency_from: str
    currency_to: str
    exchange: ExchangeService
    rate: Decimal
    result: Decimal
    updated_at: int

    @field_serializer('rate', 'result')
    def serialize_decimal(self, value: Decimal, _info):
        return f'{value:.2f}'
