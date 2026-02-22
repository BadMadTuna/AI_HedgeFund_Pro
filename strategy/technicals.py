import pandas as pd
from data.market_data import fetch_price_history

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0)).ewm(alpha=1/period, adjust=False).mean()
    return 100 - (100 / (1 + (gain / loss)))

def analyze_stock_technicals(ticker):
    """Combines raw data with math to output a clean dictionary."""
    df = fetch_price_history(ticker)
    # Apply RSI, Moving Averages, etc. here
    return {"Ticker": ticker, "RSI": calculate_rsi(df['close']).iloc[-1]}