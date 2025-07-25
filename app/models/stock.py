from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime


class HistoricalDataPoint(BaseModel):
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int


class TechnicalIndicators(BaseModel):
    rsi: Optional[float] = Field(None, description="14-period RSI")
    sma_20: Optional[float] = Field(None, description="20-day Simple Moving Average")
    sma_50: Optional[float] = Field(None, description="50-day Simple Moving Average")
    sma_200: Optional[float] = Field(None, description="200-day Simple Moving Average")
    macd: Optional[float] = Field(None, description="MACD line")
    macd_signal: Optional[float] = Field(None, description="MACD signal line")
    macd_histogram: Optional[float] = Field(None, description="MACD histogram")


class StockData(BaseModel):
    symbol: str
    market: Literal["US", "ZA", "CRYPTO"]
    company_name: str
    current_price: float
    currency: str
    change_percent: float
    volume: int
    market_cap: Optional[float] = None
    pe_ratio: Optional[float] = None
    dividend_yield: Optional[float] = None
    historical_data: List[HistoricalDataPoint]
    technical_indicators: TechnicalIndicators
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    average_volume: Optional[int] = None
    price_changes: dict = Field(default_factory=dict)  # 1m, 3m, ytd returns
    cache_info: Optional[Dict[str, Any]] = Field(default=None, description="Cache status information")


class BatchStockRequest(BaseModel):
    symbols: List[str]
    period: str = "1mo"
    interval: str = "1d"


class StockSearchResult(BaseModel):
    symbol: str
    name: str
    market: Literal["US", "ZA", "CRYPTO"]
    sector: Optional[str] = None


class StockSearchResponse(BaseModel):
    results: List[StockSearchResult]


class BatchStockResponse(BaseModel):
    stocks: List[StockData]


class ErrorResponse(BaseModel):
    error: dict
    timestamp: datetime