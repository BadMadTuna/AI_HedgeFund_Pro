import yfinance as yf

def fetch_fundamentals(ticker: str) -> dict:
    """Fetches Target Price, PEG Ratio, and Earnings Surprise completely for free using yfinance."""
    fundamentals = {"Ticker": ticker, "Provider": "yfinance"}
    
    try:
        stock = yf.Ticker(ticker)
        
        # .info returns a massive dictionary of institutional data
        info = stock.info
        
        # --- 1. TARGET PRICE ---
        fundamentals["Target_Price"] = info.get("targetMeanPrice", "N/A")
        
        # --- 2. PEG RATIO ---
        fundamentals["PEG_Ratio"] = info.get("pegRatio", "N/A")
        
        # --- 3. EARNINGS SURPRISE ---
        try:
            # yfinance returns a DataFrame of both past and future earnings dates
            earnings = stock.earnings_dates
            if earnings is not None and not earnings.empty:
                
                # Drop rows where earnings haven't happened yet (missing actual EPS)
                past_earnings = earnings.dropna(subset=['Reported EPS', 'EPS Estimate'])
                
                if not past_earnings.empty:
                    eps_actual = float(past_earnings['Reported EPS'].iloc[0])
                    eps_est = float(past_earnings['EPS Estimate'].iloc[0])
                    
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
            print(f"yfinance Earnings Error for {ticker}: {e}")
            fundamentals["Last_Earnings_Surprise_%"] = "N/A"
            
    except Exception as e:
        print(f"yfinance Core Data Error for {ticker}: {e}")
        fundamentals["Target_Price"] = "N/A"
        fundamentals["PEG_Ratio"] = "N/A"
        fundamentals["Last_Earnings_Surprise_%"] = "N/A"

    return fundamentals