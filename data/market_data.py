from openbb import obb

# Set this to "fmp" once your $19/mo API key is configured
PROVIDER = "yfinance" 

def fetch_price_history(ticker: str, days_back: int = 365):
    """Fetches historical daily candles."""
    df = obb.equity.price.historical(symbol=ticker, provider=PROVIDER).to_df()
    return df.tail(days_back)

def fetch_fundamentals(ticker: str):
    """Fetches earnings calendar and analyst targets (Requires FMP)."""
    # Example: obb.equity.fundamental.metrics(symbol=ticker, provider="fmp")
    pass