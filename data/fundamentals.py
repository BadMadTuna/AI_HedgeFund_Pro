import os
from openbb import obb

# Inject the FMP API key from your .env file
fmp_key = os.getenv("FMP_API_KEY")
if fmp_key:
    obb.user.credentials.fmp_api_key = fmp_key

def get_best_provider(ticker: str) -> str:
    """Routes US stocks to FMP, and EU stocks to Yahoo Finance"""
    eu_suffixes = ['DE', 'L', 'AS', 'PA', 'MI', 'MC', 'F']
    if "." in ticker and ticker.split(".")[1].upper() in eu_suffixes:
        return "yfinance"
    return "fmp"

def fetch_fundamentals(ticker: str) -> dict:
    provider = get_best_provider(ticker)
    fundamentals = {"Ticker": ticker, "Provider": provider}

    try:
        targets = obb.equity.estimates.price_target(symbol=ticker, provider=provider).to_df()
        fundamentals["Target_Price"] = float(targets['price_target'].iloc[0]) if not targets.empty else "N/A"
    except: fundamentals["Target_Price"] = "N/A"

    try:
        metrics = obb.equity.fundamental.metrics(symbol=ticker, provider=provider).to_df()
        fundamentals["PEG_Ratio"] = round(float(metrics['peg_ratio'].iloc[-1]), 2) if not metrics.empty and 'peg_ratio' in metrics.columns else "N/A"
    except: fundamentals["PEG_Ratio"] = "N/A"

    return fundamentals