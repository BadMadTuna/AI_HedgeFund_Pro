import gradio as gr
import threading
import time
import os
import sys
import sqlite3
from datetime import datetime

# Add root to path so we can import our modules
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)

# Ensure data directory exists for the SQLite database
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
os.makedirs(DATA_DIR, exist_ok=True)

from data.fundamentals import fetch_fundamentals
from strategy.technicals import analyze_stock_technicals
from agents.hunter_agent import generate_buy_verdict

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
        # Connect to your new SQLite database
        db_path = os.path.join(DATA_DIR, 'hedge_fund.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Failsafe: Ensure the table exists
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
        
        # Insert the trade
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

# --- APP LOGIC ---
def analyze_ticker(ticker):
    keep_alive()
    if not ticker: return "Please enter a ticker."
    
    # 1. Fetch Technicals (Price, RSI, Moving Averages)
    try:
        tech_data = analyze_stock_technicals(ticker)
    except Exception as e:
        print(f"Technicals Error: {e}")
        tech_data = {"Current_Price": "N/A", "RSI": "N/A", "SMA_50": "N/A"}
        
    # 2. Fetch Fundamentals (Targets, PEG Ratios)
    try:
        fund_data = fetch_fundamentals(ticker)
    except Exception as e:
        print(f"Fundamentals Error: {e}")
        fund_data = {"Target_Price": "N/A", "PEG_Ratio": "N/A", "Last_Earnings_Surprise_%": "N/A"}
    
    # 3. Merge them into one massive dictionary
    full_quant_payload = {**tech_data, **fund_data}
    
    # 4. Hand the complete payload to the AI
    verdict = generate_buy_verdict(ticker, full_quant_payload)
    return verdict

# --- MOBILE FRIENDLY UI ---
css_style = ".gradio-container { max-width: 100% !important; overflow-x: hidden; padding: 10px; }"

with gr.Blocks(theme=gr.themes.Soft(), css=css_style) as app:
    gr.Markdown("# 🦅 AI Hedge Fund Pro")
    
    with gr.Tab("🔍 Analyzer"):
        ticker_input = gr.Textbox(label="Enter Ticker (e.g. AAPL)")
        btn = gr.Button("Analyze", variant="primary")
        output = gr.Markdown()
        
        # --- NEW: SAVE TO PORTFOLIO WIDGET ---
        with gr.Accordion("💾 Save AI Pick to Portfolio", open=False):
            with gr.Row():
                save_qty = gr.Number(label="Shares to Buy", value=10)
                save_cost = gr.Number(label="Entry Price (€)")
                save_target = gr.Number(label="Target Price (€)", value=0)
            save_btn = gr.Button("✅ Confirm & Save to SQLite", variant="primary")
            save_msg = gr.Markdown()
            
    # Wire up the buttons
    btn.click(analyze_ticker, inputs=ticker_input, outputs=output)
    save_btn.click(save_ai_pick_to_db, inputs=[ticker_input, save_qty, save_cost, save_target], outputs=save_msg)

# Bind to 0.0.0.0 so the Elastic IP can route traffic to it
if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)