import yfinance as yf
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import pandas as pd
from concurrent.futures import ThreadPoolExecutor

from app.models.stock import StockData, HistoricalDataPoint, TechnicalIndicators, StockSearchResult
from app.config import settings
from app.services.indicator_service import IndicatorService


class StockService:
    def __init__(self):
        self.indicator_service = IndicatorService()
        self.executor = ThreadPoolExecutor(max_workers=1)  # Single worker to avoid rate limits
    
    def _determine_market(self, symbol: str) -> str:
        """Determine market type based on symbol format."""
        if symbol.endswith('.JO'):
            return "ZA"
        elif '-USD' in symbol or symbol in ['BTC-USD', 'ETH-USD', 'ADA-USD', 'XRP-USD', 'DOGE-USD']:
            return "CRYPTO"
        else:
            return "US"
    
    def _format_symbol(self, symbol: str, market: str) -> str:
        """Format symbol for yfinance based on market."""
        symbol = symbol.upper()
        
        if market == "ZA" and not symbol.endswith('.JO'):
            return f"{symbol}.JO"
        elif market == "CRYPTO" and not symbol.endswith('-USD'):
            return f"{symbol}-USD"
        
        return symbol
    
    async def get_stock_data(
        self, 
        symbol: str, 
        market: str = "US", 
        period: str = "1mo", 
        interval: str = "1d"
    ) -> Optional[StockData]:
        """Fetch stock data using basic yfinance approach."""
        try:
            formatted_symbol = self._format_symbol(symbol, market)
            
            # Run yfinance calls in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                self._fetch_basic_data,
                formatted_symbol,
                period,
                interval
            )
            
            if not result:
                return None
            
            # Extract data from enhanced result
            hist_data = result['hist_data']
            company_name = result['company_name']
            market_cap = result['market_cap']
            pe_ratio = result['pe_ratio']
            dividend_yield = result['dividend_yield']
            fifty_two_week_high = result['fifty_two_week_high']
            fifty_two_week_low = result['fifty_two_week_low']
            average_volume = result['average_volume']
            
            if hist_data.empty:
                return None
            
            # Convert historical data
            historical_data = []
            for index, row in hist_data.iterrows():
                historical_data.append(HistoricalDataPoint(
                    timestamp=index.to_pydatetime(),
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=int(row['Volume']) if pd.notna(row['Volume']) else 0
                ))
            
            # Get current price
            current_price = float(hist_data['Close'].iloc[-1])
            
            # Calculate change percent
            change_percent = 0.0
            if len(hist_data) > 1:
                prev_close = float(hist_data['Close'].iloc[-2])
                change_percent = ((current_price - prev_close) / prev_close) * 100
            
            # Basic technical indicators
            technical_indicators = await self.indicator_service.calculate_indicators(hist_data)
            
            # Volume
            volume = int(hist_data['Volume'].iloc[-1]) if pd.notna(hist_data['Volume'].iloc[-1]) else 0
            
            # Currency based on market
            currency = 'USD' if market == "US" else 'ZAR' if market == "ZA" else 'USD'
            
            # Calculate price changes for different periods
            price_changes = {}
            if len(hist_data) > 5:
                price_changes['5d'] = ((current_price - float(hist_data['Close'].iloc[-6])) / float(hist_data['Close'].iloc[-6])) * 100
            if len(hist_data) > 21:
                price_changes['1m'] = ((current_price - float(hist_data['Close'].iloc[-22])) / float(hist_data['Close'].iloc[-22])) * 100
            
            return StockData(
                symbol=formatted_symbol,
                market=market,
                company_name=company_name,
                current_price=current_price,
                currency=currency,
                change_percent=change_percent,
                volume=volume,
                market_cap=market_cap,
                pe_ratio=pe_ratio,
                dividend_yield=dividend_yield,
                historical_data=historical_data,
                technical_indicators=technical_indicators,
                fifty_two_week_high=fifty_two_week_high,
                fifty_two_week_low=fifty_two_week_low,
                average_volume=average_volume,
                price_changes=price_changes
            )
            
        except Exception as e:
            print(f"Error fetching stock data for {symbol}: {str(e)}")
            return None
    
    def _fetch_basic_data(self, symbol: str, period: str, interval: str):
        """Enhanced yfinance data fetch using full API capabilities."""
        import time
        
        try:
            # Add delay to avoid rate limits
            time.sleep(1)
            
            # Create ticker object as per yfinance docs
            ticker = yf.Ticker(symbol)
            
            # Fetch historical data
            hist_data = ticker.history(period=period, interval=interval)
            
            if hist_data.empty:
                print(f"No data returned for {symbol}")
                return None
            
            print(f"Successfully fetched {len(hist_data)} data points for {symbol}")
            
            # Get comprehensive ticker info using yfinance API methods
            try:
                # Get detailed info first (has more comprehensive data)
                info = ticker.info
                company_name = info.get('longName') or info.get('shortName') or symbol
                pe_ratio = info.get('trailingPE') or info.get('forwardPE')
                dividend_yield = info.get('dividendYield')
                
                # Use fast_info for quick access to key metrics (dot notation)
                fast_info = ticker.fast_info
                market_cap = getattr(fast_info, 'market_cap', None)
                fifty_two_week_high = getattr(fast_info, 'year_high', None)
                fifty_two_week_low = getattr(fast_info, 'year_low', None)
                average_volume = getattr(fast_info, 'ten_day_average_volume', None)
                
                # Fallback to info if fast_info doesn't have the data
                if market_cap is None:
                    market_cap = info.get('marketCap')
                if fifty_two_week_high is None:
                    fifty_two_week_high = info.get('fiftyTwoWeekHigh')
                if fifty_two_week_low is None:
                    fifty_two_week_low = info.get('fiftyTwoWeekLow')
                if average_volume is None:
                    average_volume = info.get('averageVolume') or info.get('averageVolume10days')
                
                print(f"Fetched enhanced data for {symbol}: {company_name}")
                print(f"  Market Cap: {market_cap}, PE: {pe_ratio}, 52W: {fifty_two_week_high}/{fifty_two_week_low}")
                
            except Exception as info_error:
                print(f"Could not fetch detailed info for {symbol}: {info_error}")
                # Fallback to basic data
                company_name = symbol
                market_cap = None
                pe_ratio = None
                dividend_yield = None
                fifty_two_week_high = None
                fifty_two_week_low = None
                average_volume = None
            
            return {
                'hist_data': hist_data,
                'company_name': company_name,
                'market_cap': market_cap,
                'pe_ratio': pe_ratio,
                'dividend_yield': dividend_yield,
                'fifty_two_week_high': fifty_two_week_high,
                'fifty_two_week_low': fifty_two_week_low,
                'average_volume': average_volume
            }
            
        except Exception as e:
            print(f"Error in _fetch_basic_data for {symbol}: {str(e)}")
            return None
    
    async def search_stocks(self, query: str, market: str = "ALL", limit: int = 10) -> List[StockSearchResult]:
        """Search for stocks by name or ticker."""
        results = []
        
        # Basic search with common stocks
        common_stocks = {
            "US": [
                {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
                {"symbol": "GOOGL", "name": "Alphabet Inc.", "sector": "Technology"},
                {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
                {"symbol": "AMZN", "name": "Amazon.com Inc.", "sector": "Consumer Discretionary"},
                {"symbol": "TSLA", "name": "Tesla Inc.", "sector": "Consumer Discretionary"},
                {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
                {"symbol": "META", "name": "Meta Platforms Inc.", "sector": "Technology"},
                {"symbol": "JPM", "name": "JPMorgan Chase & Co.", "sector": "Financial Services"},
            ],
            "CRYPTO": [
                {"symbol": "BTC-USD", "name": "Bitcoin", "sector": "Cryptocurrency"},
                {"symbol": "ETH-USD", "name": "Ethereum", "sector": "Cryptocurrency"},
                {"symbol": "ADA-USD", "name": "Cardano", "sector": "Cryptocurrency"},
                {"symbol": "DOGE-USD", "name": "Dogecoin", "sector": "Cryptocurrency"},
            ],
            "ZA": [
                {"symbol": "NPN.JO", "name": "Naspers Limited", "sector": "Technology"},
                {"symbol": "SHP.JO", "name": "Shoprite Holdings", "sector": "Consumer Staples"},
            ]
        }
        
        # Search logic
        markets_to_search = [market] if market != "ALL" else ["US", "CRYPTO", "ZA"]
        
        for search_market in markets_to_search:
            if search_market in common_stocks:
                for stock in common_stocks[search_market]:
                    if (query.upper() in stock["symbol"].upper() or 
                        query.lower() in stock["name"].lower()):
                        results.append(StockSearchResult(
                            symbol=stock["symbol"],
                            name=stock["name"],
                            market=search_market,
                            sector=stock["sector"]
                        ))
                        
                        if len(results) >= limit:
                            break
            
            if len(results) >= limit:
                break
        
        return results[:limit]
    
    async def get_batch_stocks(self, symbols: List[str], period: str = "1mo", interval: str = "1d") -> List[StockData]:
        """Fetch multiple stocks sequentially."""
        stock_data = []
        
        for symbol in symbols:
            market = self._determine_market(symbol)
            try:
                data = await self.get_stock_data(symbol, market, period, interval)
                if data:
                    stock_data.append(data)
            except Exception as e:
                print(f"Error fetching {symbol}: {e}")
                continue
        
        return stock_data