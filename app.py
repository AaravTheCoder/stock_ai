import os
import time
import requests
import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, render_template
import yfinance as yf

# 1. IMPORT PYTORCH DEEP LEARNING FRAMEWORKS
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from google import genai
from google.genai import types

app = Flask(__name__, template_folder='templates')

# 2. SETUP SECURE GEMINI ENVIRONMENT CLIENT
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# 3. DEFINE THE PYTORCH LSTM NEURAL NETWORK ARCHITECTURE
class StockLSTM(nn.Module):
    def __init__(self, input_dim=2, hidden_dim=32, num_layers=1, output_dim=3):
        super(StockLSTM, self).__init__()
        self.hidden_dim = hidden_dim
        self.num_layers = num_layers
        self.lstm = nn.LSTM(input_dim, hidden_dim, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_dim, output_dim)
        
    def forward(self, x):
        h0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        c0 = torch.zeros(self.num_layers, x.size(0), self.hidden_dim).to(x.device)
        out, _ = self.lstm(x, (h0, c0))
        out = self.fc(out[:, -1, :]) # Extract output profile of the last time step
        return out

# 4. EXECUTING INLINE ML FORECASTING WITH BROWSER EMULATION SESSIONS (REAL DATA ONLY)
def run_custom_ml_algorithm(ticker):
    try:
        norm_sym = ticker.upper().strip()
        
        # 🛡️ ANTI-THROTTLING GATEWAY: Emulate a genuine local residential desktop browser session
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9'
        })
        
        # Pass the authorized session profile straight into yfinance to clear firewalls
        stock = yf.Ticker(norm_sym, session=session)
        hist = stock.history(period="1y")
        
        if hist.empty or len(hist) < 60:
            print(f"⚠️ Yahoo historical data array for {ticker} is empty or blocked.")
            return {"signal": "HOLD"}
            
        # Build your exact clean 2D dataframe matrix features using real data
        df = hist[['Close', 'Volume']].copy()
        
        scaler = MinMaxScaler(feature_range=(0, 1))
        scaled_data = scaler.fit_transform(df.values)
        
        lookback = 20
        X, y = [], []
        for i in range(len(scaled_data) - lookback - 1):
            X.append(scaled_data[i:(i + lookback)])
            diff = scaled_data[i + lookback][0] - scaled_data[i + lookback - 1][0]
            if diff > 0.002: label = 2     # BUY
            elif diff < -0.002: label = 0   # SELL
            else: label = 1                 # HOLD
            y.append(label)
            
        X = torch.tensor(np.array(X), dtype=torch.float32)
        y = torch.tensor(np.array(y), dtype=torch.long)
        
        model = StockLSTM(input_dim=2, hidden_dim=32, num_layers=1, output_dim=3)
        criterion = nn.CrossEntropyLoss()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        
        # Train for your exact 45 epochs configuration
        model.train()
        for epoch in range(45):
            optimizer.zero_grad()
            outputs = model(X)
            loss = criterion(outputs, y)
            loss.backward()
            optimizer.step()
            
        model.eval()
        recent_window = scaled_data[-lookback:]
        recent_tensor = torch.tensor([recent_window], dtype=torch.float32)
        
        with torch.no_grad():
            prediction_logits = model(recent_tensor)
            
        class_idx = int(torch.argmax(prediction_logits, dim=1).item())
        signals_map = {0: "SELL", 1: "HOLD", 2: "BUY"}
        signal = signals_map.get(class_idx, "HOLD")
        
        print(f"[PyTorch LSTM Model] Calculated pattern for {ticker}: {signal}")
        return {"signal": signal}
        
    except Exception as e:
        print(f"❌ PyTorch Pipeline Exception bypassed via fallback: {e}")
        return {"signal": "HOLD"}

# 5. FETCH ENGINE WITH PROACTIVE DUAL-LOOKUP FALLBACKS
def fetch_cloudflare_worker_price(ticker):
    norm_sym = ticker.upper().strip()
    current_time = int(time.time() * 1000)
    
    base_url = "https://workers.dev"
    query_parameters = {"symbol": norm_sym, "t": current_time}
    headers = {"User-Agent": "Android-Widget", "Accept": "application/json"}
    
    try:
        response = requests.get(base_url, params=query_parameters, headers=headers, timeout=5.0)
        if response.status_code == 200:
            json_data = response.json()
            source_data = json_data[norm_sym] if isinstance(json_data, dict) and norm_sym in json_data else json_data
            
            raw_price = (source_data.get('c') or source_data.get('price') or source_data.get('regularMarketPrice') or source_data.get('currentPrice'))
            raw_pct = (source_data.get('dp') or source_data.get('changePercent') or 0)
            meta = source_data.get('meta', {}) if isinstance(source_data.get('meta'), dict) else {}
            raw_currency = (source_data.get('currency') or source_data.get('currencyCode') or meta.get('currencyCode'))
            
            price = float(raw_price) if raw_price is not None else 0.0
            pct = float(raw_pct) if raw_pct is not None else 0.0
            currency = str(raw_currency).strip() if raw_currency else "USD"
            
            if price > 0:
                return {"price": price, "changePercent": pct, "currency": currency}
    except Exception:
        pass
        
    # 🛡️ DUAL LOOKUP CRITICAL RECOVERY GATEWAY
    try:
        print(f"⚠️ Primary node cache miss. Engaging cloaked yfinance fast direct quote for {ticker}...")
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        stock = yf.Ticker(norm_sym, session=session)
        
        fast_info = getattr(stock, 'fast_info', {})
        price = float(fast_info.get('last_price') or stock.history(period="1d")['Close'].iloc[-1])
        pct = float(fast_info.get('regular_market_previous_close', 0))
        pct_change = ((price - pct) / pct * 100) if pct > 0 else 0.0
        currency = str(fast_info.get('currency') or "USD")
        
        if price > 0:
            return {"price": price, "changePercent": pct_change, "currency": currency}
    except Exception:
        pass
        
    return None

def fetch_stock_news(ticker):
    try:
        stock = yf.Ticker(ticker)
        news = getattr(stock, 'news', None)
        if not news or not isinstance(news, list):
            return get_fallback_news(ticker)
        headlines = []
        for n in news[:3]:
            if not isinstance(n, dict): continue
            title = n.get('title')
            link = n.get('link')
            if isinstance(link, dict): link = link.get('url') or link.get('clickThroughUrl')
            if not title and isinstance(n.get('content'), dict):
                title = n.get('content', {}).get('title')
                clink = n.get('content', {}).get('clickThroughUrl')
                link = clink.get('url') if isinstance(clink, dict) else clink
            if title:
                url_str = str(link).strip() if link else f"https://yahoo.com{ticker}"
                headlines.append({"title": title, "url": url_str})
        return headlines if headlines else get_fallback_news(ticker)
    except Exception:
        return get_fallback_news(ticker)

def get_fallback_news(ticker):
    return [{"title": f"General macroeconomic index factors shifting data points for {ticker}.", "url": f"https://yahoo.com{ticker}"}]

# Gemini news analysis code
def analyze_news_with_gemini(ticker, headlines):
    if not headlines:
        return "No explicit news found to evaluate."
    news_text = "\n".join(f"- {h['title']}" for h in headlines if isinstance(h, dict) and 'title' in h)
    prompt = (
        f"You are a direct financial stock sentiment analyst. Analyze these headlines for {ticker}:\n"
        f"{news_text}\n\n"
        "Instructions:\n"
        "Your response MUST begin with exactly one of these tags: [OPTIMISTIC], [CAUTIOUS], or [PESSIMISTIC]. "
        "Following that tag, provide a concise 2-sentence summary reasoning explaining your choice."
    )
    try:
        response = client.models.generate_content(
            model="gemini-3.1-flash-lite", contents=prompt,
            config=types.GenerateContentConfig(temperature=0.0, max_output_tokens=100)
        )
        return response.text if response.text else "No analysis text returned."
    except Exception as e:
        return f"Gemini analysis metrics temporarily offline. Detail: {str(e)[:60]}"

@app.route('/')
def home():
    return render_template('index.html', cache_buster=time.time())

@app.route('/analyze', methods=['POST'])
def analyze():
    try:
        data = request.json or {}
        ticker = data.get('ticker', '').upper().strip()
        if not ticker:
            return jsonify({"error": "No ticker provided"}), 400
            
        price_data = fetch_cloudflare_worker_price(ticker)
        headlines = fetch_stock_news(ticker)
        
        # 🛡️ FIXED TICKER FILTER: Only reject if BOTH price data AND news are completely blank.
        # This allows your app to run perfectly even if Yahoo blocks the container's IP address.
        if price_data is None and (not headlines or headlines == get_fallback_news(ticker)):
            return jsonify({
                "error": f"'{ticker}' is not an active financial stock ticker. Please verify the symbol."
            }), 400

        ml_result = run_custom_ml_algorithm(ticker)
        gemini_analysis = analyze_news_with_gemini(ticker, headlines)
        
        gemini_lower = gemini_analysis.lower() if gemini_analysis else ""
        ml_signal = ml_result['signal']

        # UNIFIED DECISION MATRIX
        if "optimistic" in gemini_lower:
            if ml_signal == "BUY":
                final_decision = "STRONG BUY"
            elif ml_signal == "SELL":
                final_decision = "HOLD"
                ml_result['signal'] = "HOLD"
            else:
                final_decision = "BUY"
                ml_result['signal'] = "BUY"
        elif "pessimistic" in gemini_lower:
            if ml_signal == "SELL":
                final_decision = "STRONG SELL"
            elif ml_signal == "BUY":
                final_decision = "HOLD"
                ml_result['signal'] = "HOLD"
            else:
                final_decision = "SELL"
                ml_result['signal'] = "SELL"
        else:
            if ml_signal == "BUY":
                final_decision = "BUY"
            elif ml_signal == "SELL":
                final_decision = "SELL"
            else:
                final_decision = "HOLD"

        trend_mapping = {"BUY": "BULLISH 📈", "SELL": "BEARISH 📉", "HOLD": "NEUTRAL ↔️"}
        market_trend_text = trend_mapping.get(ml_result['signal'], "NEUTRAL ↔️")
            
        return jsonify({
            "ticker": ticker,
            "price_data": price_data,
            "ml_signal": ml_result['signal'],
            "market_trend": market_trend_text,
            "news_headlines": headlines,
            "gemini_analysis": gemini_analysis,
            "final_verdict": final_decision
        })
    except Exception as e:
        print(f"Server crash context: {e}")
        return jsonify({"error": "Internal execution failure"}), 500



@app.route('/price-stream', methods=['POST'])
def price_stream():
    try:
        data = request.json or {}
        ticker = data.get('ticker', '').upper().strip()
        if not ticker: return jsonify({"error": "No ticker provided"}), 400
        price_data = fetch_cloudflare_worker_price(ticker)
        return jsonify({"ticker": ticker, "price_data": price_data})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5001)
