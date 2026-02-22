import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv(override=True)
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_buy_verdict(ticker, quant_data_dict):
    prompt = f"You are a Hedge Fund Manager. Analyze {ticker} based on this data: {quant_data_dict}. Give a verdict and a score out of 100."
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {e}"