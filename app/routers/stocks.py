from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional

from app.models.stock import (
    StockData, BatchStockRequest, BatchStockResponse, 
    StockSearchResponse, ErrorResponse
)
from app.services.stock_service import StockService
from app.utils.validators import InputValidator
from app.utils.cache import cache_manager
from app.config import settings

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])
stock_service = StockService()


@router.get("/search", response_model=StockSearchResponse)
async def search_stocks(
    query: str = Query(..., min_length=1, description="Search query (company name or ticker)"),
    market: str = Query("ALL", description="Market filter: US, ZA, CRYPTO, or ALL"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results")
):
    """Search for stocks/crypto by name or ticker symbol."""
    try:
        # Validate inputs
        market = InputValidator.validate_market(market)
        limit = InputValidator.validate_limit(limit)
        
        # Search stocks
        results = await stock_service.search_stocks(query, market, limit)
        
        return StockSearchResponse(results=results)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "SEARCH_ERROR",
                    "message": "An error occurred while searching stocks",
                    "details": {"error": str(e)}
                }
            }
        )


@router.get("/markets/status")
async def get_market_status():
    """Get current market status for different exchanges."""
    from datetime import datetime, timezone
    import pytz
    
    try:
        now_utc = datetime.now(timezone.utc)
        
        # US Market (EST/EDT)
        us_tz = pytz.timezone('US/Eastern')
        us_time = now_utc.astimezone(us_tz)
        us_open = us_time.weekday() < 5 and 9 <= us_time.hour < 16
        
        # JSE (SAST)
        za_tz = pytz.timezone('Africa/Johannesburg')
        za_time = now_utc.astimezone(za_tz)
        za_open = za_time.weekday() < 5 and 9 <= za_time.hour < 17
        
        return {
            "timestamp": now_utc.isoformat(),
            "markets": {
                "US": {
                    "is_open": us_open,
                    "local_time": us_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "next_open": "Monday 09:30 EST" if not us_open else None
                },
                "ZA": {
                    "is_open": za_open,
                    "local_time": za_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                    "next_open": "Monday 09:00 SAST" if not za_open else None
                },
                "CRYPTO": {
                    "is_open": True,
                    "local_time": now_utc.strftime("%Y-%m-%d %H:%M:%S UTC"),
                    "note": "Cryptocurrency markets operate 24/7"
                }
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "MARKET_STATUS_ERROR",
                    "message": "Unable to fetch market status",
                    "details": {"error": str(e)}
                }
            }
        )


@router.post("/batch", response_model=BatchStockResponse)
async def get_batch_stocks(request: BatchStockRequest):
    """Fetch multiple stocks in one request."""
    try:
        # Validate symbols
        validated_symbols = InputValidator.validate_symbols_list(request.symbols, max_symbols=10)
        period = InputValidator.validate_period(request.period)
        interval = InputValidator.validate_interval(request.interval)
        
        # Fetch stocks concurrently
        stock_data_list = await stock_service.get_batch_stocks(validated_symbols, period, interval)
        
        if not stock_data_list:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "NO_STOCKS_FOUND",
                        "message": "No valid stocks found for the provided symbols",
                        "details": {"symbols": validated_symbols}
                    }
                }
            )
        
        return BatchStockResponse(stocks=stock_data_list)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "BATCH_ERROR",
                    "message": "An error occurred while fetching batch stock data",
                    "details": {"error": str(e)}
                }
            }
        )


@router.get("/{symbol}", response_model=StockData)
async def get_stock(
    symbol: str,
    market: str = Query("US", description="Market type: US, ZA, or CRYPTO"),
    period: str = Query("1mo", description="Time period for historical data"),
    interval: str = Query("1d", description="Data interval")
):
    """Get individual stock/crypto data with historical prices and technical indicators."""
    try:
        # Validate inputs
        symbol = InputValidator.validate_symbol(symbol)
        market = InputValidator.validate_market(market)
        period = InputValidator.validate_period(period)
        interval = InputValidator.validate_interval(interval)
        
        # Check cache first
        cache_key = f"data:{market}:{symbol}:{period}:{interval}"
        cached_data = await cache_manager.get(cache_key)
        if cached_data:
            stock_data = StockData.model_validate(cached_data)
            # Add cache info
            stock_data.cache_info = {
                "is_cached": True,
                "cache_key": cache_key,
                "message": "This stock data was retrieved from cache"
            }
            return stock_data
        
        # Fetch stock data
        stock_data = await stock_service.get_stock_data(symbol, market, period, interval)
        
        if not stock_data:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "STOCK_NOT_FOUND",
                        "message": f"The requested stock symbol '{symbol}' was not found",
                        "details": {"symbol": symbol, "market": market}
                    }
                }
            )
        
        # Add cache info for fresh data
        stock_data.cache_info = {
            "is_cached": False,
            "cache_key": cache_key,
            "message": "This stock data was freshly fetched from yfinance"
        }
        
        # Cache the result (without cache_info to avoid storing it)
        cache_data = stock_data.model_dump()
        cache_data.pop('cache_info', None)  # Remove cache_info before caching
        await cache_manager.set(
            cache_key, 
            cache_data, 
            ttl=settings.stock_data_cache_ttl
        )
        
        return stock_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An error occurred while fetching stock data",
                    "details": {"error": str(e)}
                }
            }
        )


@router.get("/debug/{symbol}")
async def debug_ticker_data(
    symbol: str,
    market: str = Query("US", description="Market type: US, ZA, or CRYPTO")
):
    """Debug endpoint to see all available ticker data fields."""
    try:
        import yfinance as yf
        
        # Format symbol
        from app.services.stock_service import StockService
        stock_service = StockService()
        formatted_symbol = stock_service._format_symbol(symbol, market)
        
        ticker = yf.Ticker(formatted_symbol)
        
        debug_data = {
            "symbol": formatted_symbol,
            "info_keys": [],
            "fast_info_keys": [],
            "info_sample": {},
            "fast_info_sample": {},
            "available_methods": []
        }
        
        # Check info
        try:
            info = ticker.info
            debug_data["info_keys"] = list(info.keys()) if info else []
            # Get sample of key financial metrics
            key_fields = ['marketCap', 'trailingPE', 'forwardPE', 'enterpriseValue', 
                         'priceToBook', 'dividendYield', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow',
                         'averageVolume', 'averageVolume10days', 'longName', 'shortName']
            for field in key_fields:
                if field in info:
                    debug_data["info_sample"][field] = info[field]
        except Exception as e:
            debug_data["info_error"] = str(e)
        
        # Check fast_info
        try:
            fast_info = ticker.fast_info
            debug_data["fast_info_keys"] = list(fast_info.keys()) if hasattr(fast_info, 'keys') else []
            # Get all fast_info data
            if hasattr(fast_info, '__dict__'):
                debug_data["fast_info_sample"] = fast_info.__dict__
            else:
                debug_data["fast_info_sample"] = str(fast_info)
        except Exception as e:
            debug_data["fast_info_error"] = str(e)
        
        # Check available methods/properties
        debug_data["available_methods"] = [attr for attr in dir(ticker) if not attr.startswith('_')]
        
        return debug_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Debug error: {str(e)}")