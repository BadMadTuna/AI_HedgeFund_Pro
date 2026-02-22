import os
import requests
import yfinance as yf

# 1. Get the FMP API key from your .env file
fmp_key = os.getenv("FMP_API_KEY")

def fetch_fundamentals(ticker: str) -> dict:
    """Bypasses OpenBB to directly hit the FMP REST API for bulletproof data."""
    fundamentals = {"Ticker": ticker, "Provider": "fmp_direct"}
    
    # --- 1. TARGET PRICE (Free yfinance fallback) ---
    try:
        stock = yf.Ticker(ticker)
        fundamentals["Target_Price"] = stock.info.get("targetMeanPrice", "N/A")
    except Exception:
        fundamentals["Target_Price"] = "N/A"

    # Stop here if the API key isn't loaded
    if not fmp_key:
        print("CRITICAL: FMP API Key missing. Skipping FMP direct calls.")
        fundamentals["PEG_Ratio"] = "N/A"
        fundamentals["Last_Earnings_Surprise_%"] = "N/A"
        return fundamentals

    # --- 2. PEG RATIO (Direct FMP API) ---
    try:
        # Hitting the Trailing Twelve Months (TTM) Ratios endpoint
        url = f"https://financialmodelingprep.com/api/v3/ratios-ttm/{ticker}?apikey={fmp_key}"
        response = requests.get(url).json()
        
        if isinstance(response, list) and len(response) > 0:
            peg = response[0].get("pegRatioTTM")
            fundamentals["PEG_Ratio"] = round(float(peg), 2) if peg is not None else "N/A"
        else:
            fundamentals["PEG_Ratio"] = "N/A"
    except Exception as e:
        print(f"FMP PEG API Error for {ticker}: {e}")
        fundamentals["PEG_Ratio"] = "N/A"

    # --- 3. EARNINGS SURPRISE (Direct FMP API) ---
    try:
        url = f"https://financialmodelingprep.com/api/v3/earnings-surprises/{ticker}?apikey={fmp_key}"
        response = requests.get(url).json()
        
        if isinstance(response, list) and len(response) > 0:
            # FMP returns the newest quarter first at index 0
            latest = response[0]
            actual = latest.get("actualEarningResult")
            est = latest.get("estimatedEarning")
            
            if actual is not None and est is not None and est != 0:
                surprise_pct = ((actual - est) / abs(est)) * 100
                fundamentals["Last_Earnings_Surprise_%"] = round(surprise_pct, 2)
            else:
                fundamentals["Last_Earnings_Surprise_%"] = "N/A"
        else:
            fundamentals["Last_Earnings_Surprise_%"] = "N/A"
    except Exception as e:
        print(f"FMP Earnings API Error for {ticker}: {e}")
        fundamentals["Last_Earnings_Surprise_%"] = "N/A"

    return fundamentals