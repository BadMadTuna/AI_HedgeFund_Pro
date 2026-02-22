import yfinance as yf
import pandas as pd
import requests
import io

def get_sp500_tickers():
    """Scrapes the live S&P 500 list from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        r = requests.get(url, headers=headers)
        tables = pd.read_html(io.StringIO(r.text))
        # Yahoo Finance uses hyphens instead of dots (e.g., BRK.B -> BRK-B)
        return tables[0]['Symbol'].str.replace('.', '-').tolist()
    except Exception as e:
        print(f"Error fetching S&P500: {e}")
        return ["AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL"] # Fallback

def run_market_scan(max_results=10):
    """Bulk-downloads 500 stocks, calculates technicals, and ranks the top 10."""
    tickers = get_sp500_tickers()
    
    print(f"📡 Bulk downloading data for {len(tickers)} stocks...")
    # threads=True downloads data concurrently, making it incredibly fast
    data = yf.download(tickers, period="6mo", auto_adjust=True, progress=False, threads=True)
    
    # Extract just the closing prices into a 2D matrix
    close_prices = data['Close'].dropna(axis=1, how='all')
    
    # --- VECTORIZED MATH (Calculates 500 stocks instantly) ---
    curr_prices = close_prices.iloc[-1]
    sma_50 = close_prices.rolling(window=50).mean().iloc[-1]
    
    # 3-Month Momentum (Used to rank the strongest stocks)
    past_prices = close_prices.iloc[-60] if len(close_prices) >= 60 else close_prices.iloc[0]
    momentum = ((curr_prices - past_prices) / past_prices) * 100
    
    # Wilder's RSI calculation
    delta = close_prices.diff()
    gain = delta.where(delta > 0, 0.0).ewm(alpha=1/14, adjust=False).mean()
    loss = (-delta.where(delta < 0, 0.0)).ewm(alpha=1/14, adjust=False).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    curr_rsi = rsi.iloc[-1]
    
    # --- BUILD THE DASHBOARD ---
    scan_df = pd.DataFrame({
        "Price": round(curr_prices, 2),
        "SMA_50": round(sma_50, 2),
        "Momentum_%": round(momentum, 2),
        "RSI": round(curr_rsi, 2)
    })
    
    # THE QUANT FILTER: Must be in an uptrend (Price > SMA_50) but NOT overbought (RSI < 70)
    filtered = scan_df[(scan_df['Price'] > scan_df['SMA_50']) & (scan_df['RSI'] < 70)]
    
    # Rank by the strongest momentum and take the top 10
    top_picks = filtered.sort_values(by="Momentum_%", ascending=False).head(max_results)
    
    # Clean up the format for the UI
    return top_picks.reset_index().rename(columns={"Ticker": "Symbol"})