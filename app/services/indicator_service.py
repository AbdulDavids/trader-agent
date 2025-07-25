import pandas as pd
import numpy as np
from typing import Optional
from app.models.stock import TechnicalIndicators


class IndicatorService:
    
    async def calculate_indicators(self, hist_data: pd.DataFrame) -> TechnicalIndicators:
        """Calculate technical indicators from historical data."""
        if hist_data.empty or len(hist_data) < 14:
            return TechnicalIndicators()
        
        try:
            # Calculate RSI (14-period)
            rsi = self._calculate_rsi(hist_data['Close'], period=14)
            
            # Calculate Simple Moving Averages
            sma_20 = self._calculate_sma(hist_data['Close'], period=20)
            sma_50 = self._calculate_sma(hist_data['Close'], period=50)
            sma_200 = self._calculate_sma(hist_data['Close'], period=200)
            
            # Calculate MACD
            macd_line, macd_signal, macd_histogram = self._calculate_macd(hist_data['Close'])
            
            return TechnicalIndicators(
                rsi=rsi,
                sma_20=sma_20,
                sma_50=sma_50,
                sma_200=sma_200,
                macd=macd_line,
                macd_signal=macd_signal,
                macd_histogram=macd_histogram
            )
            
        except Exception as e:
            print(f"Error calculating indicators: {str(e)}")
            return TechnicalIndicators()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> Optional[float]:
        """Calculate RSI (Relative Strength Index)."""
        if len(prices) < period + 1:
            return None
        
        try:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            return float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        except Exception:
            return None
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> Optional[float]:
        """Calculate Simple Moving Average."""
        if len(prices) < period:
            return None
        
        try:
            sma = prices.rolling(window=period).mean()
            return float(sma.iloc[-1]) if not pd.isna(sma.iloc[-1]) else None
        except Exception:
            return None
    
    def _calculate_macd(self, prices: pd.Series, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        """Calculate MACD (Moving Average Convergence Divergence)."""
        if len(prices) < slow_period + signal_period:
            return None, None, None
        
        try:
            # Calculate EMAs
            ema_fast = prices.ewm(span=fast_period).mean()
            ema_slow = prices.ewm(span=slow_period).mean()
            
            # MACD line
            macd_line = ema_fast - ema_slow
            
            # Signal line
            macd_signal = macd_line.ewm(span=signal_period).mean()
            
            # Histogram
            macd_histogram = macd_line - macd_signal
            
            return (
                float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None,
                float(macd_signal.iloc[-1]) if not pd.isna(macd_signal.iloc[-1]) else None,
                float(macd_histogram.iloc[-1]) if not pd.isna(macd_histogram.iloc[-1]) else None
            )
        except Exception:
            return None, None, None