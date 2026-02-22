from openbb import obb

def fetch_price_history(ticker: str, days_back: int = 365):
    """Fetches historical daily candles using yfinance."""
    try:
        # We use yfinance for raw price data to save FMP API credits
        df = obb.equity.price.historical(symbol=ticker, provider="yfinance").to_df()
        return df.tail(days_back)
    except Exception as e:
        print(f"Error fetching price for {ticker}: {e}")
        return None