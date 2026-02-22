import os
import yfinance as yf
from openbb import obb

# 1. Inject the FMP API key from your .env file
fmp_key = os.getenv("FMP_API_KEY")
if fmp_key:
    obb.user.credentials.fmp_api_key = fmp_key

def fetch_fundamentals(ticker: str) -> dict:
    """Uses paid FMP for deep ratios, and free yfinance for the missing Target Price."""
    fundamentals = {"Ticker": ticker, "Provider": "fmp_hybrid"}
    
    # --- 1. ANALYST PRICE TARGETS (Free Fallback) ---
    try:
        # FMP Starter tier does not include targets, so we grab it from yfinance
        stock = yf.Ticker(ticker)
        fundamentals["Target_Price"] = stock.info.get("targetMeanPrice", "N/A")
    except Exception as e:
        print(f"YF Target Price Error for {ticker}: {e}")
        fundamentals["Target_Price"] = "N/A"

    # --- 2. VALUATION METRICS (Paid FMP Data) ---
    try:
        # OpenBB v4 uses .ratios() and the column 'price_to_earnings_growth'
        ratios = obb.equity.fundamental.ratios(symbol=ticker, provider="fmp", period="annual").to_df()
        
        if not ratios.empty and 'price_to_earnings_growth' in ratios.columns:
            # Drop empty rows and grab the most recent PEG ratio
            valid_pegs = ratios['price_to_earnings_growth'].dropna()
            if not valid_pegs.empty:
                fundamentals["PEG_Ratio"] = round(float(valid_pegs.iloc[-1]), 2)
            else:
                fundamentals["PEG_Ratio"] = "N/A"
        else:
            fundamentals["PEG_Ratio"] = "N/A"
            
    except Exception as e:
        print(f"FMP PEG Ratio Error for {ticker}: {e}")
        fundamentals["PEG_Ratio"] = "N/A"

    try:
        # Pull the historical earnings calendar
        earnings = obb.equity.calendar.earnings(symbol=ticker, provider="fmp").to_df()
        
        # Ensure the required columns exist
        if not earnings.empty and 'eps_actual' in earnings.columns and 'eps_estimated' in earnings.columns:
            
            # Drop future dates where earnings haven't happened yet
            past_earnings = earnings.dropna(subset=['eps_actual', 'eps_estimated'])
            
            if not past_earnings.empty:
                eps_actual = float(past_earnings['eps_actual'].iloc[0])
                eps_est = float(past_earnings['eps_estimated'].iloc[0])
                
                # Calculate the percentage beat/miss
                if eps_est != 0:
                    surprise_pct = ((eps_actual - eps_est) / abs(eps_est)) * 100
                    fundamentals["Last_Earnings_Surprise_%"] = round(surprise_pct, 2)
                else:
                    fundamentals["Last_Earnings_Surprise_%"] = "N/A"
            else:
                fundamentals["Last_Earnings_Surprise_%"] = "N/A"
        else:
            fundamentals["Last_Earnings_Surprise_%"] = "N/A"
            
    except Exception as e:
        print(f"FMP Earnings Error for {ticker}: {e}")
        fundamentals["Last_Earnings_Surprise_%"] = "N/A"

    return fundamentals