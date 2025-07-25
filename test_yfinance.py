#!/usr/bin/env python3
"""
Simple yfinance test script to verify basic functionality
"""

import sys
import time

def test_yfinance():
    """Test basic yfinance functionality"""
    print("Testing yfinance...")
    print(f"Python: {sys.executable}")
    
    try:
        import yfinance as yf
        print("✓ yfinance imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import yfinance: {e}")
        return False
    
    # Test symbols to try - start with one
    symbols = ['MSFT']
    
    for symbol in symbols:
        print(f"\n--- Testing {symbol} ---")
        try:
            # Create ticker
            ticker = yf.Ticker(symbol)
            print(f"✓ Ticker created for {symbol}")
            
            # Wait longer before making request
            print("Waiting 5 seconds before request...")
            time.sleep(5)
            
            # Try minimal request first
            print(f"Fetching 5 day history with minimal parameters...")
            hist = ticker.history(period="5d")
            
            if hist.empty:
                print(f"✗ No data returned for {symbol}")
                
                # Try alternative approach
                print("Trying different period...")
                time.sleep(3)
                hist = ticker.history(period="1mo")
                
                if hist.empty:
                    print(f"✗ Still no data for {symbol}")
                else:
                    print(f"✓ Got {len(hist)} data points with 1mo period")
            else:
                print(f"✓ Got {len(hist)} data points")
                print(f"  Columns: {list(hist.columns)}")
                if 'Close' in hist.columns:
                    latest_close = hist['Close'].iloc[-1]
                    print(f"  Latest close: ${latest_close:.2f}")
                    print(f"  Date range: {hist.index[0]} to {hist.index[-1]}")
                    
        except Exception as e:
            print(f"✗ Error with {symbol}: {type(e).__name__}: {e}")
    
    print("\n--- Trying alternative test ---")
    try:
        # Try a very basic test
        print("Testing with simple ticker creation...")
        msft = yf.Ticker("MSFT")
        print("Waiting 10 seconds...")
        time.sleep(10)
        
        # Try to get just today's data
        print("Getting today's data...")
        today_data = msft.history(period="1d", interval="1d")
        print(f"Today data shape: {today_data.shape}")
        
    except Exception as e:
        print(f"Alternative test failed: {e}")
    
    return True

if __name__ == "__main__":
    test_yfinance() 