from enum import Enum
from decimal import Decimal

from pydantic import BaseModel


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
