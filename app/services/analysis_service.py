import json
from typing import Optional, Dict, Any, List
from datetime import datetime
from openai import AsyncOpenAI
import logging

from app.models.analysis import StockAnalysisOutput, StockAnalysis, ComparisonResponse, ComparisonResult
from app.models.stock import StockData
from app.config import settings
from app.utils.cache import CacheManager

# Set up logging for token usage
logger = logging.getLogger(__name__)
token_logger = logging.getLogger("token_usage")


class AnalysisService:
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.cache = CacheManager()
        self.total_tokens_used = 0
        self.total_cost = 0.0
    
    def _log_token_usage(self, completion, operation: str, symbol: str = None):
        """Log token usage and estimated cost for OpenAI API calls."""
        try:
            if hasattr(completion, 'usage') and completion.usage:
                prompt_tokens = completion.usage.prompt_tokens
                completion_tokens = completion.usage.completion_tokens
                total_tokens = completion.usage.total_tokens
                
                # GPT-4o-mini pricing (as of 2024)
                # Input: $0.150 per 1M tokens, Output: $0.600 per 1M tokens
                input_cost = (prompt_tokens / 1_000_000) * 0.150
                output_cost = (completion_tokens / 1_000_000) * 0.600
                total_cost = input_cost + output_cost
                
                # Update running totals
                self.total_tokens_used += total_tokens
                self.total_cost += total_cost
                
                # Log detailed token usage
                token_info = {
                    "operation": operation,
                    "symbol": symbol,
                    "model": settings.openai_model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens,
                    "estimated_cost_usd": round(total_cost, 6),
                    "input_cost_usd": round(input_cost, 6),
                    "output_cost_usd": round(output_cost, 6),
                    "session_total_tokens": self.total_tokens_used,
                    "session_total_cost_usd": round(self.total_cost, 6),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                # Log to both regular logger and token-specific logger
                logger.info(f"🪙 Token Usage - {operation}" + (f" ({symbol})" if symbol else "") + 
                           f": {total_tokens} tokens, ${total_cost:.6f}")
                token_logger.info(f"TOKEN_USAGE: {json.dumps(token_info)}")
                
                print(f"🪙 OpenAI Token Usage - {operation}" + (f" for {symbol}" if symbol else ""))
                print(f"   📊 Tokens: {prompt_tokens:,} input + {completion_tokens:,} output = {total_tokens:,} total")
                print(f"   💰 Cost: ${input_cost:.6f} + ${output_cost:.6f} = ${total_cost:.6f}")
                print(f"   📈 Session Total: {self.total_tokens_used:,} tokens, ${self.total_cost:.6f}")
                
                return token_info
            else:
                logger.warning(f"No usage data available for {operation}")
                return None
                
        except Exception as e:
            logger.error(f"Error logging token usage for {operation}: {str(e)}")
            return None
    
    async def analyze_asset(self, symbol: str, market: str, stock_data: StockData) -> Optional[StockAnalysis]:
        """Generate AI-powered analysis for a stock/crypto asset."""
        # Check cache first
        cache_key = f"analysis:{market}:{symbol}"
        cached_result = await self.cache.get(cache_key)
        if cached_result:
            logger.info(f"📋 Using cached analysis for {symbol} (no tokens used)")
            analysis = StockAnalysis.model_validate(cached_result)
            # Add cache info to the analysis
            analysis.cache_info = {
                "is_cached": True,
                "cache_key": cache_key,
                "message": "This analysis was retrieved from cache"
            }
            return analysis
        
        try:
            # Build market-specific analysis prompt
            prompt = self._build_analysis_prompt(stock_data, market)
            
            # Call GPT-4o-mini with structured output
            print(f"🚀 Making OpenAI API call for {symbol}...")
            completion = await self.client.beta.chat.completions.parse(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system", 
                        "content": self._get_system_prompt(market)
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                response_format=StockAnalysisOutput,
                temperature=0.3,
                max_tokens=2000
            )
            print(f"✅ OpenAI API call completed for {symbol}")
            
            # Log token usage
            self._log_token_usage(completion, "stock_analysis", symbol)
            
            if not completion.choices[0].message.parsed:
                return None
            
            ai_output = completion.choices[0].message.parsed
            
            # Create full analysis object
            analysis = StockAnalysis(
                symbol=symbol,
                market=market,
                timestamp=datetime.utcnow(),
                recommendation=ai_output.recommendation,
                confidence_score=ai_output.confidence_score,
                target_price=ai_output.target_price,
                analysis_summary=ai_output.analysis_summary,
                key_points=ai_output.key_points,
                price_targets=ai_output.price_targets,
                risks=self._extract_risks(ai_output.key_points),
                opportunities=self._extract_opportunities(ai_output.key_points),
                cache_info={
                    "is_cached": False,
                    "cache_key": cache_key,
                    "message": "This analysis was freshly generated using AI",
                    "tokens_used": completion.usage.total_tokens if completion.usage else 0,
                    "cost_usd": self.total_cost
                }
            )
            
            # Cache the result
            await self.cache.set(
                cache_key, 
                analysis.model_dump(), 
                ttl=settings.analysis_cache_ttl
            )
            
            return analysis
            
        except Exception as e:
            error_msg = f"Error generating analysis for {symbol}: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {e.__dict__ if hasattr(e, '__dict__') else 'No details'}")
            return None
    
    def _get_system_prompt(self, market: str) -> str:
        """Get market-specific system prompt."""
        base_prompt = "You are a professional financial analyst with 15+ years of experience in market analysis."
        
        if market == "CRYPTO":
            return f"{base_prompt} You specialize in cryptocurrency analysis, understanding blockchain fundamentals, tokenomics, and crypto market dynamics. You stay updated on regulatory developments and technological innovations in the crypto space."
        elif market == "ZA":
            return f"{base_prompt} You specialize in South African (JSE) market analysis, understanding local economic conditions, currency impacts (ZAR), and JSE-specific factors. You're familiar with South African companies and their business environments."
        else:
            return f"{base_prompt} You specialize in US stock market analysis, understanding American companies, SEC regulations, and US economic indicators. You're well-versed in fundamental and technical analysis of US equities."
    
    def _build_analysis_prompt(self, stock_data: StockData, market: str) -> str:
        """Build comprehensive analysis prompt with all available data."""
        
        # Format technical indicators
        tech_indicators = []
        if stock_data.technical_indicators.rsi:
            rsi_interpretation = "overbought" if stock_data.technical_indicators.rsi > 70 else "oversold" if stock_data.technical_indicators.rsi < 30 else "neutral"
            tech_indicators.append(f"RSI: {stock_data.technical_indicators.rsi:.2f} ({rsi_interpretation})")
        
        if stock_data.technical_indicators.sma_20:
            price_vs_sma20 = "above" if stock_data.current_price > stock_data.technical_indicators.sma_20 else "below"
            tech_indicators.append(f"20-day SMA: {stock_data.technical_indicators.sma_20:.2f} (price is {price_vs_sma20})")
        
        if stock_data.technical_indicators.sma_50:
            price_vs_sma50 = "above" if stock_data.current_price > stock_data.technical_indicators.sma_50 else "below"
            tech_indicators.append(f"50-day SMA: {stock_data.technical_indicators.sma_50:.2f} (price is {price_vs_sma50})")
        
        if stock_data.technical_indicators.macd and stock_data.technical_indicators.macd_signal:
            macd_signal = "bullish" if stock_data.technical_indicators.macd > stock_data.technical_indicators.macd_signal else "bearish"
            tech_indicators.append(f"MACD: {stock_data.technical_indicators.macd:.4f} (signal: {macd_signal})")
        
        # Format price changes
        price_changes = []
        for period, change in stock_data.price_changes.items():
            price_changes.append(f"{period}: {change:+.2f}%")
        
        # Build market-specific prompt
        if market == "CRYPTO":
            market_cap_str = f"${stock_data.market_cap:,}" if stock_data.market_cap else "N/A"
            low_52_str = f"${stock_data.fifty_two_week_low:.2f}" if stock_data.fifty_two_week_low else "N/A"
            high_52_str = f"${stock_data.fifty_two_week_high:.2f}" if stock_data.fifty_two_week_high else "N/A"
            
            prompt = f"""
Analyze the cryptocurrency {stock_data.company_name} ({stock_data.symbol}) based on the following data:

CURRENT DATA:
- Current Price: ${stock_data.current_price:,.2f}
- 24h Change: {stock_data.change_percent:+.2f}%
- Volume: {stock_data.volume:,}
- Market Cap: {market_cap_str}

PRICE PERFORMANCE:
{' | '.join(price_changes) if price_changes else 'Limited historical data'}

TECHNICAL INDICATORS:
{' | '.join(tech_indicators) if tech_indicators else 'Insufficient data for indicators'}

52-Week Range: {low_52_str} - {high_52_str}

Please provide a comprehensive analysis considering:
1. Technical analysis based on the indicators and price action
2. Market sentiment and crypto-specific factors
3. Risk assessment for cryptocurrency volatility
4. Potential price targets (bearish, neutral, bullish scenarios)

Provide a clear BUY/HOLD/SELL recommendation with confidence score and reasoning.
"""
        else:
            # Stock analysis prompt
            market_cap_str = f"${stock_data.market_cap:,}" if stock_data.market_cap else "N/A"
            avg_volume_str = f"{stock_data.average_volume:,}" if stock_data.average_volume else "N/A"
            dividend_str = f"{stock_data.dividend_yield:.2%}" if stock_data.dividend_yield else "N/A"
            low_52_str = f"${stock_data.fifty_two_week_low:.2f}" if stock_data.fifty_two_week_low else "N/A"
            high_52_str = f"${stock_data.fifty_two_week_high:.2f}" if stock_data.fifty_two_week_high else "N/A"
            
            prompt = f"""
Analyze the stock {stock_data.company_name} ({stock_data.symbol}) based on the following data:

CURRENT DATA:
- Current Price: ${stock_data.current_price:,.2f}
- Daily Change: {stock_data.change_percent:+.2f}%
- Volume: {stock_data.volume:,}
- Average Volume: {avg_volume_str}

VALUATION METRICS:
- Market Cap: {market_cap_str}
- P/E Ratio: {stock_data.pe_ratio or 'N/A'}
- Dividend Yield: {dividend_str}

PRICE PERFORMANCE:
{' | '.join(price_changes) if price_changes else 'Limited historical data'}

TECHNICAL INDICATORS:
{' | '.join(tech_indicators) if tech_indicators else 'Insufficient data for indicators'}

52-Week Range: {low_52_str} - {high_52_str}

Please provide a comprehensive analysis considering:
1. Technical analysis based on the indicators and price trends
2. Fundamental valuation using P/E ratio and market cap
3. Risk assessment and market conditions
4. Price targets for different scenarios (bearish, neutral, bullish)

Provide a clear BUY/HOLD/SELL recommendation with confidence score and detailed reasoning.
"""
        
        return prompt
    
    def _extract_risks(self, key_points: List) -> List[str]:
        """Extract risk-related points from analysis."""
        risks = []
        for point in key_points:
            if point.category == "risk" or point.sentiment == "negative":
                risks.append(point.point)
        return risks
    
    def _extract_opportunities(self, key_points: List) -> List[str]:
        """Extract opportunity-related points from analysis."""
        opportunities = []
        for point in key_points:
            if (point.category in ["fundamental", "market"] and 
                point.sentiment == "positive"):
                opportunities.append(point.point)
        return opportunities
    
    async def compare_stocks(self, symbols: List[str], stock_data_list: List[StockData]) -> Optional[ComparisonResponse]:
        """Compare multiple stocks and provide recommendation."""
        if len(symbols) != len(stock_data_list) or len(symbols) < 2:
            return None
        
        try:
            # Build comparison prompt
            comparison_data = []
            for i, (symbol, data) in enumerate(zip(symbols, stock_data_list)):
                comparison_data.append(f"""
{symbol} ({data.company_name}):
- Price: ${data.current_price:.2f} ({data.change_percent:+.2f}%)
- Market Cap: ${data.market_cap:,} (if available)
- P/E Ratio: {data.pe_ratio or 'N/A'}
- RSI: {data.technical_indicators.rsi:.2f} (if available)
- Volume: {data.volume:,}
""")
            
            prompt = f"""
Compare the following stocks and determine which one offers the best investment opportunity:

{chr(10).join(comparison_data)}

Provide:
1. A score (0-10) for each stock based on technical and fundamental factors
2. Key strengths and weaknesses for each
3. Your top recommendation with clear reasoning
4. Consider factors like valuation, momentum, risk, and growth potential
"""
            
            # For simplicity, using regular completion instead of structured output for comparison
            completion = await self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional stock analyst providing comparative analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            # Log token usage
            symbols_str = ", ".join(symbols)
            self._log_token_usage(completion, "stock_comparison", symbols_str)
            
            # Parse the response (simplified - in production you'd want structured output)
            response_text = completion.choices[0].message.content
            
            # Create comparison results (simplified scoring)
            comparison_results = []
            for symbol, data in zip(symbols, stock_data_list):
                # Simplified scoring based on basic metrics
                score = self._calculate_simple_score(data)
                comparison_results.append(ComparisonResult(
                    symbol=symbol,
                    score=score,
                    strengths=[f"Current price: ${data.current_price:.2f}"],
                    weaknesses=["Limited analysis in demo mode"]
                ))
            
            # Sort by score and pick winner
            comparison_results.sort(key=lambda x: x.score, reverse=True)
            winner = comparison_results[0].symbol
            
            return ComparisonResponse(
                comparison=comparison_results,
                winner=winner,
                reasoning=[response_text] if response_text else ["Analysis completed"],
                timestamp=datetime.utcnow()
            )
            
        except Exception as e:
            error_msg = f"Error comparing stocks: {str(e)}"
            print(error_msg)
            logger.error(error_msg)
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception details: {e.__dict__ if hasattr(e, '__dict__') else 'No details'}")
            return None
    
    def _calculate_simple_score(self, data: StockData) -> float:
        """Calculate a simple score for stock comparison."""
        score = 5.0  # Base score
        
        # Adjust based on RSI
        if data.technical_indicators.rsi:
            if 30 <= data.technical_indicators.rsi <= 70:
                score += 1.0  # Good RSI range
            elif data.technical_indicators.rsi < 30:
                score += 1.5  # Potentially oversold
            else:
                score -= 1.0  # Overbought
        
        # Adjust based on price momentum
        if data.change_percent > 2:
            score += 0.5
        elif data.change_percent < -2:
            score -= 0.5
        
        # Adjust based on P/E ratio
        if data.pe_ratio and 10 <= data.pe_ratio <= 25:
            score += 1.0  # Reasonable valuation
        
        return max(0, min(10, score))  # Clamp between 0-10
    
    def get_token_usage_stats(self) -> Dict[str, Any]:
        """Get current session token usage statistics."""
        return {
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost, 6),
            "model": settings.openai_model,
            "cost_per_1k_tokens": {
                "input": 0.150 / 1000,  # $0.000150 per 1K input tokens
                "output": 0.600 / 1000  # $0.000600 per 1K output tokens
            },
            "session_start": datetime.utcnow().isoformat()
        }
    
    def reset_token_usage_stats(self):
        """Reset token usage counters for new session."""
        self.total_tokens_used = 0
        self.total_cost = 0.0
        logger.info("🔄 Token usage statistics reset")