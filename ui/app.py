import gradio as gr
import threading
import time
import os
import sys

# Add root to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from data.fundamentals import fetch_fundamentals
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

# --- APP LOGIC ---
def analyze_ticker(ticker):
    keep_alive()
    if not ticker: return "Please enter a ticker."
    
    data = fetch_fundamentals(ticker)
    verdict = generate_buy_verdict(ticker, data)
    return verdict

# --- MOBILE FRIENDLY UI ---
css_style = ".gradio-container { max-width: 100% !important; overflow-x: hidden; padding: 10px; }"

with gr.Blocks(theme=gr.themes.Soft(), css=css_style) as app:
    gr.Markdown("# 🦅 AI Hedge Fund Pro")
    ticker_input = gr.Textbox(label="Enter Ticker (e.g. AAPL)")
    btn = gr.Button("Analyze", variant="primary")
    output = gr.Markdown()
    
    btn.click(analyze_ticker, inputs=ticker_input, outputs=output)

# Bind to 0.0.0.0 so the Elastic IP can route traffic to it
if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860)