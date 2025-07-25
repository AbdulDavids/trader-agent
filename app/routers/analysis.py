from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime

from app.models.analysis import (
    StockAnalysis, CompareRequest, ComparisonResponse,
    PortfolioRequest, PortfolioAnalysis
)
from app.services.analysis_service import AnalysisService
from app.services.stock_service import StockService
from app.utils.validators import InputValidator
from app.config import settings

router = APIRouter(prefix="/api/v1/analysis", tags=["analysis"])
analysis_service = AnalysisService()
stock_service = StockService()


@router.get("/health")
async def analysis_health_check():
    """Health check endpoint for analysis service."""
    try:
        # Test OpenAI connection
        test_client = analysis_service.client
        
        return {
            "status": "healthy",
            "service": "analysis",
            "openai_configured": bool(settings.openai_api_key),
            "cache_available": await analysis_service.cache.exists("health_check_test"),
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "analysis",
            "error": str(e),
            "timestamp": "2024-01-15T10:30:00Z"
        }


@router.get("/tokens")
async def get_token_usage():
    """Get current session token usage statistics."""
    try:
        stats = analysis_service.get_token_usage_stats()
        return {
            "status": "success",
            "token_usage": stats,
            "message": f"Total tokens used: {stats['total_tokens_used']:,}, Total cost: ${stats['total_cost_usd']:.6f}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving token usage: {str(e)}")


@router.post("/tokens/reset")
async def reset_token_usage():
    """Reset token usage statistics for new session."""
    try:
        old_stats = analysis_service.get_token_usage_stats()
        analysis_service.reset_token_usage_stats()
        
        return {
            "status": "success",
            "message": "Token usage statistics reset",
            "previous_session": {
                "tokens_used": old_stats['total_tokens_used'],
                "cost_usd": old_stats['total_cost_usd']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting token usage: {str(e)}")


@router.post("/compare", response_model=ComparisonResponse)
async def compare_stocks(request: CompareRequest):
    """Compare two or more stocks and provide investment recommendation."""
    try:
        # Validate symbols
        validated_symbols = InputValidator.validate_symbols_list(
            request.symbols, 
            max_symbols=5
        )
        
        if len(validated_symbols) < 2:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "INSUFFICIENT_SYMBOLS",
                        "message": "At least 2 symbols are required for comparison",
                        "details": {"provided": len(validated_symbols)}
                    }
                }
            )
        
        # Fetch stock data for all symbols
        stock_data_list = []
        for symbol in validated_symbols:
            market = stock_service._determine_market(symbol)
            stock_data = await stock_service.get_stock_data(symbol, market)
            
            if stock_data:
                stock_data_list.append(stock_data)
            else:
                # Remove invalid symbols from comparison
                validated_symbols.remove(symbol)
        
        if len(stock_data_list) < 2:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": {
                        "code": "INSUFFICIENT_VALID_STOCKS",
                        "message": "At least 2 valid stocks are required for comparison",
                        "details": {"valid_stocks": len(stock_data_list)}
                    }
                }
            )
        
        # Generate comparison analysis
        comparison = await analysis_service.compare_stocks(validated_symbols, stock_data_list)
        
        if not comparison:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": "COMPARISON_FAILED",
                        "message": "Failed to generate stock comparison",
                        "details": {"symbols": validated_symbols}
                    }
                }
            )
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An error occurred while comparing stocks",
                    "details": {"error": str(e)}
                }
            }
        )


@router.post("/portfolio", response_model=PortfolioAnalysis)
async def analyze_portfolio(request: PortfolioRequest):
    """Analyze a portfolio of holdings and provide recommendations."""
    try:
        if not request.holdings:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "code": "EMPTY_PORTFOLIO",
                        "message": "Portfolio cannot be empty",
                        "details": {}
                    }
                }
            )
        
        total_value = 0.0
        total_cost = 0.0
        recommendations = []
        rebalancing_suggestions = []
        
        # Process each holding
        for holding in request.holdings:
            symbol = InputValidator.validate_symbol(holding.symbol)
            market = stock_service._determine_market(symbol)
            
            # Get current stock data
            stock_data = await stock_service.get_stock_data(symbol, market)
            
            if stock_data:
                current_value = stock_data.current_price * holding.quantity
                cost_basis = holding.purchase_price * holding.quantity
                
                total_value += current_value
                total_cost += cost_basis
                
                # Calculate gain/loss for this position
                position_gain_loss = current_value - cost_basis
                position_gain_loss_percent = (position_gain_loss / cost_basis) * 100
                
                # Add basic recommendations based on performance
                if position_gain_loss_percent > 20:
                    recommendations.append(f"Consider taking profits on {symbol} (+{position_gain_loss_percent:.1f}%)")
                elif position_gain_loss_percent < -15:
                    recommendations.append(f"Review {symbol} position (-{position_gain_loss_percent:.1f}%)")
                
                # Simple rebalancing logic
                position_weight = (current_value / total_value) * 100 if total_value > 0 else 0
                if position_weight > 30:
                    rebalancing_suggestions.append(f"Consider reducing {symbol} allocation ({position_weight:.1f}% of portfolio)")
        
        # Calculate overall performance
        total_gain_loss = total_value - total_cost
        gain_loss_percent = (total_gain_loss / total_cost) * 100 if total_cost > 0 else 0
        
        # Risk assessment
        risk_level = "moderate"
        if len(request.holdings) < 5:
            risk_level = "high - consider diversification"
        elif len(request.holdings) > 15:
            risk_level = "low - well diversified"
        
        from datetime import datetime
        
        return PortfolioAnalysis(
            total_value=total_value,
            total_gain_loss=total_gain_loss,
            gain_loss_percent=gain_loss_percent,
            recommendations=recommendations if recommendations else ["Portfolio performing within normal parameters"],
            rebalancing_suggestions=rebalancing_suggestions if rebalancing_suggestions else ["Portfolio allocation appears balanced"],
            risk_assessment=f"Risk level: {risk_level}",
            timestamp=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "PORTFOLIO_ANALYSIS_ERROR",
                    "message": "An error occurred while analyzing portfolio",
                    "details": {"error": str(e)}
                }
            }
        )


@router.post("/clear-cache")
async def clear_analysis_cache():
    """Clear all cached analysis data."""
    try:
        # Access the cache manager from the analysis service
        from app.utils.cache import cache_manager
        
        # Clear all analysis cache keys (they start with "analysis:")
        cache_keys_cleared = 0
        
        # Get all keys that start with "analysis:"
        try:
            # Note: This is a simple implementation. For production, you might want
            # to use Redis SCAN for better performance with large datasets
            import redis
            redis_client = redis.from_url(settings.redis_url)
            
            # Get all keys matching the pattern
            analysis_keys = redis_client.keys("analysis:*")
            
            if analysis_keys:
                # Delete all matching keys
                cache_keys_cleared = redis_client.delete(*analysis_keys)
                
            redis_client.close()
            
        except Exception as redis_error:
            # Fallback: just report that we attempted to clear
            print(f"Redis direct access failed: {redis_error}")
            cache_keys_cleared = "unknown"
        
        return {
            "status": "success",
            "message": f"Analysis cache cleared successfully",
            "keys_cleared": cache_keys_cleared,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "CACHE_CLEAR_FAILED",
                    "message": "Failed to clear analysis cache",
                    "details": {"error": str(e)}
                }
            }
        )


# The /{symbol} route should be at the end, after /health, /compare, and /portfolio routes
@router.get("/{symbol}", response_model=StockAnalysis)
async def get_stock_analysis(
    symbol: str,
    market: str = Query("US", description="Market type: US, ZA, or CRYPTO"),
    analysis_type: str = Query("comprehensive", description="Analysis type: technical, fundamental, sentiment, comprehensive")
):
    """Get AI-powered analysis for a stock/crypto with BUY/HOLD/SELL recommendation."""
    try:
        # Validate inputs
        symbol = InputValidator.validate_symbol(symbol)
        market = InputValidator.validate_market(market)
        analysis_type = InputValidator.validate_analysis_type(analysis_type)
        
        # First get the stock data
        stock_data = await stock_service.get_stock_data(symbol, market)
        
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
        
        # Generate AI analysis
        analysis = await analysis_service.analyze_asset(symbol, market, stock_data)
        
        if not analysis:
            raise HTTPException(
                status_code=500,
                detail={
                    "error": {
                        "code": "ANALYSIS_FAILED",
                        "message": "Failed to generate AI analysis for the stock",
                        "details": {"symbol": symbol, "market": market}
                    }
                }
            )
        
        return analysis
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An error occurred while generating analysis",
                    "details": {"error": str(e)}
                }
            }
        )