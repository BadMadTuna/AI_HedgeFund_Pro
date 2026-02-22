import gradio as gr
import threading
import time
import os
import sys
import sqlite3
import pandas as pd
from datetime import datetime

# --- PATH CONFIG ---
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# Ensure data directory exists for SQLite
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

# --- CUSTOM MODULES ---
from data.fundamentals import fetch_fundamentals
from strategy.technicals import analyze_stock_technicals
from agents.hunter_agent import generate_buy_verdict
from strategy.scanner import run_market_scan

# --- AUTO SHUTDOWN LOGIC (Saves AWS Costs) ---
LAST_INTERACTION = time.time()
def keep_alive():
    global LAST_INTERACTION
    LAST_INTERACTION = time.time()

def auto_shutdown_monitor():
    while True:
        # 45 minutes of inactivity = shut down the EC2 instance
        if time.time() - LAST_INTERACTION > 2700: 
            print("Idle timeout. Shutting down EC2...")
            os.system("sudo shutdown -h now")
        time.sleep(60)

threading.Thread(target=auto_shutdown_monitor, daemon=True).start()

# --- SQLITE DATABASE LOGIC ---
def save_ai_pick_to_db(ticker, qty, cost, target):
    """Safely saves a high-conviction AI pick to the SQLite database."""
    keep_alive()
    if not ticker: 
        return "⚠️ Please enter a ticker first."
    
    try:
        db_path = os.path.join(DATA_DIR, 'hedge_fund.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT NOT NULL,
                cost REAL,
                quantity REAL,
                target REAL,
                date TEXT,
                status TEXT
            )
        ''')
        
        date_str = datetime.now().strftime('%Y-%m-%d')
        cursor.execute('''
            INSERT INTO portfolio (ticker, cost, quantity, target, date, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (ticker.upper(), float(cost), float(qty), float(target), date_str, 'Open'))
        
        conn.commit()
        conn.close()
        return f"✅ **{ticker.upper()}** successfully saved to SQLite Portfolio!"
    except Exception as e:
        return f"❌ Database Error: {str(e)}"

# --- SINGLE TICKER ANALYZER ---
def analyze_ticker(ticker):
    keep_alive()
    if not ticker: return "Please enter a ticker."
    
    # 1. Fetch Technicals
    try:
        tech_data = analyze_stock_technicals(ticker)
    except Exception as e:
        print(f"Technicals Error: {e}")
        tech_data = {"Current_Price": "Data Error", "RSI": "Data Error", "SMA_50": "Data Error"}
        
    # 2. Fetch Fundamentals
    try:
        fund_data = fetch_fundamentals(ticker)
    except Exception as e:
        print(f"Fundamentals Error: {e}")
        fund_data = {"Target_Price": "N/A", "PEG_Ratio": "N/A", "Last_Earnings_Surprise_%": "N/A"}
    
    # 3. Merge & Analyze
    full_quant_payload = {**tech_data, **fund_data}
    verdict = generate_buy_verdict(ticker, full_quant_payload)
    return verdict

# --- SCANNER LOGIC ---
def execute_quant_scan():
    """Runs the pure-math S&P 500 scanner"""
    keep_alive()
    df = run_market_scan(max_results=10)
    # Ensure AI_Verdict column exists
    if not df.empty and "AI_Verdict" not in df.columns:
        df["AI_Verdict"] = "Pending..."
    return df

def batch_ai_analysis(df):
    """Passes the scanner survivors to Gemini"""
    keep_alive()
    if df is None or df.empty:
        return df
        
    if "AI_Verdict" not in df.columns:
        df['AI_Verdict'] = "⏳ Processing..."
    
    for index, row in df.iterrows():
        ticker = row['Symbol']
        verdict = analyze_ticker(ticker) 
        
        # Parse the AI's label
        if "BUY" in verdict.upper(): df.at[index, 'AI_Verdict'] = "🟢 BUY"
        elif "AVOID" in verdict.upper(): df.at[index, 'AI_Verdict'] = "🔴 AVOID"
        else: df.at[index, 'AI_Verdict'] = "⚪ HOLD / CAUTION"
        
    return df

# --- UI LAYOUT ---
css_style = ".gradio-container { max-width: 100% !important; overflow-x: hidden; padding: 10px; }"

with gr.Blocks(theme=gr.themes.Soft(), css=css_style) as app:
    gr.Markdown("# 🦅 AI Hedge Fund Pro")
    
    # TAB 1: The Quantamental Funnel
    with gr.Tab("📡 S&P 500 Scanner"):
        with gr.Row():
            scan_btn = gr.Button("1️⃣ Run Quant Filter (Top 10)", variant="primary")
            ai_batch_btn = gr.Button("2️⃣ Run AI Analysis on Results", variant="secondary")
            
        scan_results = gr.Dataframe(headers=["Symbol", "Price", "SMA_50", "Momentum_%", "RSI", "AI_Verdict"])
        
        scan_btn.click(execute_quant_scan, outputs=scan_results)
        ai_batch_btn.click(batch_ai_analysis, inputs=scan_results, outputs=scan_results)
        
    # TAB 2: Deep Dive & Save
    with gr.Tab("🔍 Analyzer"):
        ticker_input = gr.Textbox(label="Enter Ticker (e.g. AAPL)")
        btn = gr.Button("Analyze", variant="primary")
        output = gr.Markdown()
        
        with gr.Accordion("💾 Save AI Pick to Portfolio", open=False):
            with gr.Row():
                save_qty = gr.Number(label="Shares to Buy", value=10)
                save_cost = gr.Number(label="Entry Price (€)")
                save_target = gr.Number(label="Target Price (€)", value=0)
            save_btn = gr.Button("✅ Confirm & Save to SQLite", variant="primary")
            save_msg = gr.Markdown()
            
    # Wire the analyzer and DB buttons
    btn.click(analyze_ticker, inputs=ticker_input, outputs=output)
    save_btn.click(save_ai_pick_to_db, inputs=[ticker_input, save_qty, save_cost, save_target], outputs=save_msg)

# Bind to 0.0.0.0 so the Elastic IP can route traffic to it
if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)