import re
from typing import List, Optional
from fastapi import HTTPException


class InputValidator:
    
    @staticmethod
    def validate_symbol(symbol: str) -> str:
        """Validate and normalize stock symbol."""
        if not symbol or len(symbol.strip()) == 0:
            raise HTTPException(status_code=400, detail="Symbol cannot be empty")
        
        symbol = symbol.upper().strip()
        
        # Allow alphanumeric characters, dots, and hyphens
        if not re.match(r'^[A-Z0-9.-]+$', symbol):
            raise HTTPException(
                status_code=400, 
                detail="Invalid symbol format. Only letters, numbers, dots, and hyphens allowed"
            )
        
        if len(symbol) > 10:
            raise HTTPException(status_code=400, detail="Symbol too long (max 10 characters)")
        
        return symbol
    
    @staticmethod
    def validate_market(market: str) -> str:
        """Validate market parameter."""
        valid_markets = ["US", "ZA", "CRYPTO", "ALL"]
        market = market.upper().strip()
        
        if market not in valid_markets:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid market. Must be one of: {', '.join(valid_markets)}"
            )
        
        return market
    
    @staticmethod
    def validate_period(period: str) -> str:
        """Validate period parameter for yfinance."""
        valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        
        if period not in valid_periods:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid period. Must be one of: {', '.join(valid_periods)}"
            )
        
        return period
    
    @staticmethod
    def validate_interval(interval: str) -> str:
        """Validate interval parameter for yfinance."""
        valid_intervals = [
            "1m", "2m", "5m", "15m", "30m", "60m", "90m", 
            "1h", "1d", "5d", "1wk", "1mo", "3mo"
        ]
        
        if interval not in valid_intervals:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid interval. Must be one of: {', '.join(valid_intervals)}"
            )
        
        return interval
    
    @staticmethod
    def validate_symbols_list(symbols: List[str], max_symbols: int = 10) -> List[str]:
        """Validate list of symbols."""
        if not symbols:
            raise HTTPException(status_code=400, detail="Symbols list cannot be empty")
        
        if len(symbols) > max_symbols:
            raise HTTPException(
                status_code=400, 
                detail=f"Too many symbols. Maximum {max_symbols} allowed"
            )
        
        validated_symbols = []
        for symbol in symbols:
            validated_symbols.append(InputValidator.validate_symbol(symbol))
        
        return validated_symbols
    
    @staticmethod
    def validate_analysis_type(analysis_type: str) -> str:
        """Validate analysis type parameter."""
        valid_types = ["technical", "fundamental", "sentiment", "comprehensive"]
        analysis_type = analysis_type.lower().strip()
        
        if analysis_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid analysis type. Must be one of: {', '.join(valid_types)}"
            )
        
        return analysis_type
    
    @staticmethod
    def validate_limit(limit: int, max_limit: int = 50) -> int:
        """Validate limit parameter."""
        if limit < 1:
            raise HTTPException(status_code=400, detail="Limit must be at least 1")
        
        if limit > max_limit:
            raise HTTPException(
                status_code=400, 
                detail=f"Limit too high. Maximum {max_limit} allowed"
            )
        
        return limit