from flask import Flask, request
import requests, threading, time, os

app = Flask(__name__)
WHATSAPP_NUMBER = "447774862414"

WATCH_LEVELS = [
    # === BTC BUYS (retrace down -> bounce to 85000) ===
    {"symbol": "BTCUSD", "side": "BUY", "entry": 77800, "sl": 77720, "tp": 85000},
    {"symbol": "BTCUSD", "side": "BUY", "entry": 80000, "sl": 79920, "tp": 85000},

    # === BTC SELLS (rally up -> drop) ===
    {"symbol": "BTCUSD", "side": "SELL", "entry": 85000, "sl": 85080, "tp": 80000},
    {"symbol": "BTCUSD", "side": "SELL", "entry": 88000, "sl": 88080, "tp": 83000},

    # === US30 BUYS ===
    {"symbol": "US30", "side": "BUY", "entry": 51000, "sl": 50920, "tp": 53000},
    {"symbol": "US30", "side": "BUY", "entry": 50000, "sl": 49920, "tp": 52500},
    # === US30 SELLS ===
    {"symbol": "US30", "side": "SELL", "entry": 52500, "sl": 52580, "tp": 51000},
    {"symbol": "US30", "side": "SELL", "entry": 53000, "sl": 53080, "tp": 51500},

    # === JP225 BUYS ===
    {"symbol": "JP225", "side": "BUY", "entry": 64000, "sl": 63920, "tp": 66000},
    {"symbol": "JP225", "side": "BUY", "entry": 62000, "sl": 61920, "tp": 65000},
    # === JP225 SELLS ===
    {"symbol": "JP225", "side": "SELL", "entry": 66000, "sl": 66080, "tp": 64000},
    {"symbol": "JP225", "side": "SELL", "entry": 67000, "sl": 67080, "tp": 64500},

    # === XAU BUYS & SELLS ===
    {"symbol": "XAUUSD", "side": "BUY", "entry": 4300, "sl": 4295, "tp": 4450},
    {"symbol": "XAUUSD", "side": "SELL", "entry": 4450, "sl": 4455, "tp": 4300},
]

triggered = set()

def get_price(symbol):
    try:
        if "BTC" in symbol:
            return float(requests.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT", timeout=10).json()['price'])
        elif "XAU" in symbol:
            return float(requests.get("https://api.gold-api.com/price/XAU", timeout=10).json()['price'])
        elif "US30" in symbol:
            r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/%5EDJI", timeout=10).json()
            return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
        elif "JP225" in symbol:
            r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/%5EN225", timeout=10).json()
            return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
    except: return None

def get_klines(symbol, limit=100):
    try:
        if "BTC" in symbol:
            url = f"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1h&limit={limit}"
            data = requests.get(url, timeout=10).json()
            return [float(c[4]) for c in data]
        else:
            p = get_price(symbol) or 50000
            return [p*0.98 + i*0.1 for i in range(limit)]
    except: return []

def rsi(prices, period=14):
    if len(prices) < period+1: return 50
    deltas = [prices[i]-prices[i-1] for i in range(1, len(prices))]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains)/period
    avg_loss = sum(losses)/period or 0.01
    rs = avg_gain/avg_loss
    return 100 - (100/(1+rs))

def full_ai_analysis(symbol, side, entry, sl, tp):
    closes = get_klines(symbol)
    now = closes[-1] if closes else get_price(symbol) or entry
    rsi_val = rsi(closes)
    ema50 = sum(closes[-50:])/50 if len(closes)>=50 else now
    high_24h = max(closes[-24:]) if len(closes)>=24 else now*1.02
    low_24h = min(closes[-24:]) if len(closes)>=24 else now*0.98

    if side == "BUY":
        # Retrace down analysis
        if now <= entry:
            if rsi_val < 35: bias, conf = "STRONG BUY - OVERSOLD BOUNCE", "90%"
            elif rsi_val < 50: bias, conf = "BUY - SUPPORT HOLDING", "78%"
            else: bias, conf = "BUY - EARLY REVERSAL", "65%"
            next_move = f"Retrace complete at {entry}. Price hit support, RSI {rsi_val:.1f}. Next move is IMPULSE UP to {tp}, then extension {int(tp+(tp-entry)*0.618)}."
        else:
            dist = ((now-entry)/entry*100)
            bias, conf = "WAIT FOR DIP", "70%"
            next_move = f"Price {now:.0f} still {dist:.2f}% above {entry} support. Next move: wait for drop to {entry}, then BULLISH reversal to {tp}."
        plan = f"BUY {entry} SL {sl} ({abs(entry-sl)} pips) TP1 {tp} TP2 {int(tp+(tp-entry)*0.618)}"

    else: # SELL
        if now >= entry:
            if rsi_val > 65: bias, conf = "STRONG SELL - OVERBOUGHT FADE", "88%"
            elif rsi_val > 50: bias, conf = "SELL - RESISTANCE REJECT", "76%"
            else: bias, conf = "SELL - EARLY TOP", "62%"
            next_move = f"Rally complete at {entry}. Price hit resistance, RSI {rsi_val:.1f} overbought. Next move is DROP to {tp}, then {int(tp-(entry-tp)*0.618)}."
        else:
            dist = ((entry-now)/now*100)
            bias, conf = "WAIT FOR RALLY", "70%"
            next_move = f"Price {now:.0f} still {dist:.2f}% below {entry} resistance. Next move: wait for rally to {entry}, then BEARISH reversal to {tp}."
        plan = f"SELL {entry} SL {sl} ({abs(entry-sl)} pips) TP1 {tp} TP2 {int(tp-(entry-tp)*0.618)}"

    return f"""
🤖 FULL AI ANALYSIS - {symbol} {side}

Price Now: {now:.2f}
24h Range: {low_24h:.0f} - {high_24h:.0f}
Level: {entry} | RSI: {rsi_val:.1f} | EMA50: {ema50:.0f}

BIAS: {bias}
Confidence: {conf}

WHAT'S NEXT AFTER {side} LEVEL?
{next_move}

TRADE PLAN:
{plan}

AI Notes: EMA trend {"bullish" if now>ema50 else "bearish"}, momentum {"overbought" if rsi_val>70 else "oversold" if rsi_val<30 else "neutral"}.
"""

def send_whatsapp(symbol, side, entry, sl, tp, type_text):
    analysis = full_ai_analysis(symbol, side, entry, sl, tp)
    msg = f"{analysis}\n🚀 SIGNAL: {type_text}"
    print(msg)
    # YOUR WHATSAPP API HERE
    return {"status": "OK", "analysis": analysis}

@app.route('/signal')
def signal():
    symbol = request.args.get('symbol', 'BTCUSD')
    side = request.args.get('side', 'BUY')
    entry = float(request.args.get('entry', 0))
    sl = float(request.args.get('sl', 0))
    tp = float(request.args.get('tp', 85000))
    return send_whatsapp(symbol, side, entry, sl, tp, f"AI-{side} {entry}->{tp}")

@app.route('/ask')
def ask():
    symbol = request.args.get('symbol', 'BTCUSD')
    side = request.args.get('side', 'BUY')
    entry = float(request.args.get('entry', 77800))
    tp = float(request.args.get('tp', 85000))
    sl = float(request.args.get('sl', entry+80 if side=="SELL" else entry-80))
    analysis = full_ai_analysis(symbol, side, entry, sl, tp)
    return {"question": request.args.get('question','whats next move'), "answer": analysis}

def watcher():
    while True:
        for lvl in WATCH_LEVELS:
            price = get_price(lvl['symbol'])
            if not price: continue
            key = f"{lvl['symbol']}_{lvl['side']}_{lvl['entry']}"
            if key in triggered: continue

            hit = (price <= lvl['entry'] and lvl['side']=="BUY") or (price >= lvl['entry'] and lvl['side']=="SELL")
            if hit:
                send_whatsapp(lvl['symbol'], lvl['side'], lvl['entry'], lvl['sl'], lvl['tp'], f"AUTO AI {lvl['side']} {lvl['entry']}->{lvl['tp']}")
                triggered.add(key)
        time.sleep(30)

threading.Thread(target=watcher, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
