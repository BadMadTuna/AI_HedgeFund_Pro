import os
from openbb import obb

# 1. Inject the FMP API key from your .env file
fmp_key = os.getenv("FMP_API_KEY")
if fmp_key:
    obb.user.credentials.fmp_api_key = fmp_key
else:
    print("CRITICAL: FMP API Key missing from environment!")

def fetch_fundamentals(ticker: str) -> dict:
    """Fetches fundamental data using your paid FMP plan."""
    fundamentals = {"Ticker": ticker, "Provider": "fmp"}
    
    # --- 1. ANALYST PRICE TARGETS (OpenBB v4 Syntax) ---
    try:
        # The correct v4 endpoint for FMP consensus targets
        targets = obb.equity.estimates.consensus(symbol=ticker, provider="fmp").to_df()
        
        if not targets.empty and 'target_consensus' in targets.columns:
            fundamentals["Target_Price"] = float(targets['target_consensus'].iloc[0])
        else:
            fundamentals["Target_Price"] = "N/A"
            
    except Exception as e:
        print(f"FMP Target Price Error for {ticker}: {e}")
        fundamentals["Target_Price"] = "N/A"

    # --- 2. VALUATION METRICS (PEG Ratio) ---
    try:
        metrics = obb.equity.fundamental.metrics(symbol=ticker, provider="fmp").to_df()
        
        if not metrics.empty and 'peg_ratio' in metrics.columns:
            fundamentals["PEG_Ratio"] = round(float(metrics['peg_ratio'].iloc[-1]), 2)
        else:
            fundamentals["PEG_Ratio"] = "N/A"
            
    except Exception as e:
        print(f"FMP PEG Ratio Error for {ticker}: {e}")
        fundamentals["PEG_Ratio"] = "N/A"

    return fundamentals