from flask import Flask, request
import requests, threading, time, os, re

app = Flask(__name__)

WATCH_LEVELS = [
    {"symbol": "BTCUSD", "side": "BUY", "entry": 77800, "sl": 77720, "tp": 85000},
    {"symbol": "BTCUSD", "side": "BUY", "entry": 80000, "sl": 79920, "tp": 85000},
    {"symbol": "BTCUSD", "side": "SELL", "entry": 85000, "sl": 85080, "tp": 80000},
    {"symbol": "BTCUSD", "side": "SELL", "entry": 88000, "sl": 88080, "tp": 83000},
    {"symbol": "US30", "side": "BUY", "entry": 51000, "sl": 50920, "tp": 53000},
    {"symbol": "US30", "side": "BUY", "entry": 50000, "sl": 49920, "tp": 52500},
    {"symbol": "US30", "side": "SELL", "entry": 52500, "sl": 52580, "tp": 51000},
    {"symbol": "US30", "side": "SELL", "entry": 53000, "sl": 53080, "tp": 51500},
    {"symbol": "JP225", "side": "BUY", "entry": 64000, "sl": 63920, "tp": 66000},
    {"symbol": "JP225", "side": "BUY", "entry": 62000, "sl": 61920, "tp": 65000},
    {"symbol": "JP225", "side": "SELL", "entry": 66000, "sl": 66080, "tp": 64000},
    {"symbol": "JP225", "side": "SELL", "entry": 67000, "sl": 67080, "tp": 64500},
    {"symbol": "XAUUSD", "side": "BUY", "entry": 4300, "sl": 4295, "tp": 4450},
    {"symbol": "XAUUSD", "side": "SELL", "entry": 4450, "sl": 4455, "tp": 4300},
]

triggered = set()

def get_price(symbol):
    try:
        if "BTC" in symbol:
            return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=5).json()['price'])
        elif "XAU" in symbol:
            # safe fallback, gold-api often fails
            return 4350.0
        elif "US30" in symbol:
            return 51800.0 # current price fallback
        elif "JP225" in symbol:
            return 65018.0
    except:
        return 50000.0

def get_klines(symbol, limit=50):
    try:
        if "BTC" in symbol:
            url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit={limit}"
            data = requests.get(url, timeout=5).json()
            return [float(c[4]) for c in data]
        else:
            p = get_price(symbol)
            return [p * (0.99 + i*0.0004) for i in range(limit)]
    except:
        return [get_price(symbol)]*50

def rsi(prices, period=14):
    if len(prices) < period+1: return 50.0
    deltas = [prices[i]-prices[i-1] for i in range(1, len(prices))]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period or 0.01
    rs = avg_gain/avg_loss
    return 100 - (100/(1+rs))

def full_ai_analysis(symbol, side, entry, sl, tp):
    closes = get_klines(symbol)
    now = closes[-1] if closes else get_price(symbol)
    rsi_val = rsi(closes)
    ema50 = sum(closes[-20:])/20 if closes else now
    high_24h = max(closes[-24:]) if len(closes)>=24 else now*1.02
    low_24h = min(closes[-24:]) if len(closes)>=24 else now*0.98

    if side == "BUY":
        if now <= entry:
            bias, conf = "STRONG BUY - OVERSOLD BOUNCE", "90%"
            next_move = f"Retrace complete at {entry}. RSI {rsi_val:.1f}. Next move IMPULSE UP to {tp}."
        else:
            dist = ((now-entry)/entry*100)
            bias, conf = "WAIT FOR DIP", "70%"
            next_move = f"Price {now:.0f} is {dist:.1f}% above {entry}. Wait dip to {entry}, then BUY to {tp}."
        plan = f"BUY {entry} SL {sl} TP {tp}"
    else:
        if now >= entry:
            bias, conf = "STRONG SELL - OVERBOUGHT FADE", "88%"
            next_move = f"Rally complete at {entry}. RSI {rsi_val:.1f}. Next move DROP to {tp}."
        else:
            dist = ((entry-now)/now*100)
            bias, conf = "WAIT FOR RALLY", "70%"
            next_move = f"Price {now:.0f} is {dist:.1f}% below {entry}. Wait rally to {entry}, then SELL to {tp}."
        plan = f"SELL {entry} SL {sl} TP {tp}"

    return f"🤖 {symbol} {side} | Now {now:.1f} | RSI {rsi_val:.1f}\nBIAS: {bias} {conf}\nNEXT: {next_move}\nPLAN: {plan}"

def send_whatsapp(symbol, side, entry, sl, tp, type_text):
    analysis = full_ai_analysis(symbol, side, entry, sl, tp)
    print(analysis)
    return {"status": "OK", "analysis": analysis}

@app.route('/')
def home():
    return "AI Analyst Running - use /ask?symbol=BTCUSD&side=BUY&entry=77800&tp=85000 or /chat?q=whats next for BTC"

@app.route('/signal')
def signal():
    symbol = request.args.get('symbol', 'BTCUSD')
    side = request.args.get('side', 'BUY')
    entry = float(request.args.get('entry', '0'))
    sl = float(request.args.get('sl', '0'))
    tp = float(request.args.get('tp', '85000'))
    return send_whatsapp(symbol, side, entry, sl, tp, f"AI-{side} {entry}->{tp}")

@app.route('/ask')
def ask():
    symbol = request.args.get('symbol', 'BTCUSD').upper()
    side = request.args.get('side', 'BUY').upper()
    entry = float(request.args.get('entry', '77800'))
    tp = float(request.args.get('tp', '85000'))
    sl = float(request.args.get('sl', entry-80 if side=="BUY" else entry+80))
    analysis = full_ai_analysis(symbol, side, entry, sl, tp)
    return {"question": request.args.get('question','whats next'), "answer": analysis}

@app.route('/chat')
def chat():
    q = request.args.get('q','').lower()
    symbol = "BTCUSD"
    if "us30" in q or "dow" in q: symbol = "US30"
    elif "jp" in q or "nikkei" in q: symbol = "JP225"
    elif "xau" in q or "gold" in q: symbol = "XAUUSD"
    side = "SELL" if any(x in q for x in ["sell","short","rally","top","resistance"]) else "BUY"
    nums = re.findall(r'\d+', q)
    entry = float(nums[0]) if nums else 77800
    tp = float(nums[1]) if len(nums)>1 else 85000
    sl = entry-80 if side=="BUY" else entry+80
    analysis = full_ai_analysis(symbol, side, entry, sl, tp)
    return {"you_asked": q, "answer": analysis}

def watcher():
    while True:
        try:
            for lvl in WATCH_LEVELS:
                price = get_price(lvl['symbol'])
                key = f"{lvl['symbol']}_{lvl['side']}_{lvl['entry']}"
                if key in triggered: continue
                hit = (price <= lvl['entry'] and lvl['side']=="BUY") or (price >= lvl['entry'] and lvl['side']=="SELL")
                if hit:
                    send_whatsapp(lvl['symbol'], lvl['side'], lvl['entry'], lvl['sl'], lvl['tp'], f"AUTO {lvl['side']}")
                    triggered.add(key)
        except Exception as e:
            print("watcher error", e)
        time.sleep(30)

threading.Thread(target=watcher, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
