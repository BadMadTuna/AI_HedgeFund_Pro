import google.generativeai as genai
import os

genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel('gemini-2.5-flash')

def generate_buy_verdict(ticker, quant_data_dict):
    """Takes the clean dictionary from the strategy layer and asks for a verdict."""
    prompt = f"Analyze {ticker} based on this exact data: {quant_data_dict}. Give a verdict."
    response = model.generate_content(prompt)
    return response.text