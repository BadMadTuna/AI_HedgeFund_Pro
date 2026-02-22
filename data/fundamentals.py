from openbb import obb

PROVIDER = "fmp" # Change to "yfinance" if testing for free first

def fetch_fundamentals(ticker: str) -> dict:
    fundamentals = {"Ticker": ticker}
    try:
        targets = obb.equity.estimates.price_target(symbol=ticker, provider=PROVIDER).to_df()
        fundamentals["Target_Price"] = float(targets['price_target'].iloc[0]) if not targets.empty else "N/A"
    except: fundamentals["Target_Price"] = "N/A"
    # (Add the rest of the FMP logic we built in the previous step here)
    return fundamentals