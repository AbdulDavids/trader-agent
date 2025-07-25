from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Dict, Any
from datetime import datetime


class AnalysisPoint(BaseModel):
    category: Literal["technical", "fundamental", "market", "risk"]
    point: str = Field(max_length=200)
    sentiment: Literal["positive", "negative", "neutral"]


class PriceTargets(BaseModel):
    bearish: float = Field(gt=0)
    neutral: float = Field(gt=0) 
    bullish: float = Field(gt=0)


class StockAnalysisOutput(BaseModel):
    recommendation: Literal["BUY", "HOLD", "SELL"]
    confidence_score: float = Field(ge=0, le=1, description="Confidence from 0 to 1")
    target_price: float = Field(gt=0)
    analysis_summary: str = Field(max_length=500)
    key_points: List[AnalysisPoint] = Field(max_items=10)
    price_targets: PriceTargets


class StockAnalysis(BaseModel):
    symbol: str
    market: Literal["US", "ZA", "CRYPTO"]
    timestamp: datetime
    recommendation: Literal["BUY", "HOLD", "SELL"]
    confidence_score: float = Field(ge=0, le=1)
    target_price: float
    analysis_summary: str
    key_points: List[AnalysisPoint]
    price_targets: PriceTargets
    risks: List[str] = Field(default_factory=list)
    opportunities: List[str] = Field(default_factory=list)
    cache_info: Optional[Dict[str, Any]] = Field(default=None, description="Cache status information")


class CompareRequest(BaseModel):
    symbols: List[str] = Field(min_items=2, max_items=5)
    metrics: List[Literal["performance", "valuation", "growth", "risk"]] = Field(default=["performance", "valuation"])


class ComparisonResult(BaseModel):
    symbol: str
    score: float = Field(ge=0, le=10)
    strengths: List[str]
    weaknesses: List[str]


class ComparisonResponse(BaseModel):
    comparison: List[ComparisonResult]
    winner: str
    reasoning: List[str]
    timestamp: datetime


class PortfolioHolding(BaseModel):
    symbol: str
    quantity: float = Field(gt=0)
    purchase_price: float = Field(gt=0)


class PortfolioRequest(BaseModel):
    holdings: List[PortfolioHolding] = Field(min_items=1)


class PortfolioAnalysis(BaseModel):
    total_value: float
    total_gain_loss: float
    gain_loss_percent: float
    recommendations: List[str]
    rebalancing_suggestions: List[str]
    risk_assessment: str
    timestamp: datetime