import yfinance as yf
import pandas as pd

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    return 100 - (100 / (1 + (gain / loss)))

def analyze_stock_technicals(ticker: str) -> dict:
    try:
        # Bypassing OpenBB to use pure yfinance for bulletproof price delivery
        stock = yf.Ticker(ticker)
        df = stock.history(period="1y")
        
        if df.empty:
            return {"Current_Price": "Data Error", "RSI": "Data Error", "SMA_50": "Data Error"}
            
        curr_price = round(df['Close'].iloc[-1], 2)
        rsi = round(calculate_rsi(df['Close']).iloc[-1], 2)
        sma_50 = round(df['Close'].rolling(50).mean().iloc[-1], 2)
        
        return {"Current_Price": curr_price, "RSI": rsi, "SMA_50": sma_50}
    except Exception as e:
        print(f"Technicals Error for {ticker}: {e}")
        return {"Current_Price": "Data Error", "RSI": "Data Error", "SMA_50": "Data Error"}