import pandas as pd
from data.market_data import fetch_price_history

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    return 100 - (100 / (1 + (gain / loss)))

def analyze_stock_technicals(ticker: str) -> dict:
    df = fetch_price_history(ticker)
    
    if df is None or df.empty:
        return {"Current_Price": "Data Error", "RSI": "Data Error"}
        
    curr_price = round(df['close'].iloc[-1], 2)
    rsi = round(calculate_rsi(df['close']).iloc[-1], 2)
    sma_50 = round(df['close'].rolling(50).mean().iloc[-1], 2)
    
    return {"Current_Price": curr_price, "RSI": rsi, "SMA_50": sma_50}