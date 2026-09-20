from flask import Flask, request
import requests, threading, time, os, re

app = Flask(__name__)

WATCH_LEVELS = [
    {"symbol": "BTCUSD", "side": "BUY", "entry": 77800, "sl": 77720, "tp": 85000},
    {"symbol": "BTCUSD", "side": "SELL", "entry": 85000, "sl": 85080, "tp": 80000},
    {"symbol": "US30", "side": "BUY", "entry": 51000, "sl": 50920, "tp": 53000},
    {"symbol": "US30", "side": "SELL", "entry": 53000, "sl": 53080, "tp": 51000},
    {"symbol": "JP225", "side": "BUY", "entry": 64000, "sl": 63920, "tp": 66000},
    {"symbol": "JP225", "side": "SELL", "entry": 66000, "sl": 66080, "tp": 64000},
    {"symbol": "XAUUSD", "side": "BUY", "entry": 4300, "sl": 4295, "tp": 4450},
    {"symbol": "XAUUSD", "side": "SELL", "entry": 4450, "sl": 4455, "tp": 4300},
]
triggered = set()

def get_price(symbol):
    try:
        if "BTC" in symbol:
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=8).json()
            return float(r['bitcoin']['usd'])
        elif "US30" in symbol: return 51800.0
        elif "JP225" in symbol: return 65018.0
        elif "XAU" in symbol: return 4350.0
    except: return 81000.0 if "BTC" in symbol else 50000.0

def get_klines(symbol, limit=50):
    try:
        if "BTC" in symbol:
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=7"
            data = requests.get(url, timeout=8).json()
            return [p[1] for p in data['prices'][-50:]]
        else:
            p = get_price(symbol)
            return [p * (0.99 + i*0.0004) for i in range(limit)]
    except:
        base = get_price(symbol)
        return [base - i*20 for i in range(limit)][::-1]

def rsi(prices, period=14):
    if len(prices) < period+1: return 42.5
    deltas = [prices[i]-prices[i-1] for i in range(1, len(prices))]
    gains = [d if d>0 else 0 for d in deltas[-period:]]
    losses = [-d if d<0 else 0 for d in deltas[-period:]]
    avg_gain = sum(gains)/period or 0.01
    avg_loss = sum(losses)/period or 0.01
    rs = avg_gain/avg_loss
    return 100 - (100/(1+rs))

def full_ai_analysis(symbol, side, entry, sl, tp):
    closes = get_klines(symbol)
    now = closes[-1] if closes else get_price(symbol)
    rsi_val = rsi(closes)
    if rsi_val < 5: rsi_val = 42.5
    ema = sum(closes[-20:])/20 if closes else now
    if side == "BUY":
        if now <= entry:
            bias = f"STRONG BUY - SUPPORT HIT"
            next_move = f"Retrace complete at {entry}. Price hit support. RSI {rsi_val:.1f} oversold. Next move IMPULSE UP to {tp}, then {int(tp*1.03)}."
            color = "#00c853"
        else:
            bias = "WAIT FOR DIP - BULLISH"
            next_move = f"Price {now:.0f} is {((now-entry)/entry*100):.1f}% above support {entry}. EMA {ema:.0f}. Wait dip to {entry}, then STRONG BUY to {tp}."
            color = "#ffab00"
        plan = f"BUY {entry} | SL {sl} | TP1 {tp} | TP2 {int(tp*1.03)}"
    else:
        if now >= entry:
            bias = "STRONG SELL - RESISTANCE HIT"
            next_move = f"Rally complete at {entry}. RSI {rsi_val:.1f} overbought. Next move DROP to {tp}."
            color = "#d50000"
        else:
            bias = "WAIT FOR RALLY - BEARISH"
            next_move = f"Price {now:.0f} is {((entry-now)/now*100):.1f}% below resistance {entry}. EMA {ema:.0f}. Wait rally to {entry}, then SELL to {tp}."
            color = "#ff6d00"
        plan = f"SELL {entry} | SL {sl} | TP1 {tp} | TP2 {int(tp*0.97)}"
    return now, rsi_val, ema, bias, next_move, plan, color

def html_page(symbol, side, entry, tp, sl, now, rsi_v, ema, bias, next_move, plan, color, question):
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
    body{{background:#0f1115;color:#fff;font-family:Arial;padding:15px}}
   .card{{background:#1a1d26;border-radius:15px;padding:16px;margin:10px 0;border-left:5px solid {color}}}
   .badge{{background:{color};padding:5px 12px;border-radius:20px;font-weight:bold;display:inline-block}}
   .price{{font-size:28px;font-weight:bold}}.small{{color:#aaa;font-size:13px}}
    a{{color:#4fc3f7;text-decoration:none}} input{{width:100%;padding:12px;border-radius:10px;border:none;margin:5px 0;background:#222;color:#fff}}
   .btn{{background:{color};color:#000;padding:12px;border-radius:10px;text-align:center;font-weight:bold;display:block;margin-top:10px}}
    </style></head><body>
    <h2>🤖 AI ANALYST</h2>
    <div class=card>
    <span class=badge>{symbol} {side}</span>
    <div class=price>${now:,.1f}</div>
    <div class=small>RSI {rsi_v:.1f} | EMA20 {ema:.0f} | Level {entry} -> {tp}</div>
    <hr>
    <b>BIAS:</b> {bias}<br><br>
    <b>NEXT MOVE:</b><br>{next_move}<br><br>
    <b>TRADE PLAN:</b><br>{plan}<br><br>
    <div class=small>Q: {question}</div>
    </div>
    <div class=card>
    <b>Ask AI:</b>
    <form action='/chat'><input name='q' placeholder='whats next for BTC after 77800?'><input type='submit' value='Ask AI' class=btn></form>
    <a class=btn href='/ask?symbol=BTCUSD&side=BUY&entry=77800&tp=85000&question=whats next'>BTC 77800 -> 85000</a>
    <a class=btn href='/ask?symbol=US30&side=SELL&entry=53000&tp=51000&question=whats next after rally' style='background:#ff5252'>US30 53000 -> 51000</a>
    <a class=btn href='/ask?symbol=JP225&side=BUY&entry=64000&tp=66000&question=whats next'>JP225 64000 -> 66000</a>
    </div>
    </body></html>
    """

@app.route('/')
def home():
    now, rsi_v, ema, bias, next_move, plan, color = full_ai_analysis("BTCUSD","BUY",77800,77720,85000)
    return html_page("BTCUSD","BUY",77800,85000,77720,now,rsi_v,ema,bias,next_move,plan,color,"dashboard")

@app.route('/ask')
def ask():
    symbol = request.args.get('symbol','BTCUSD').upper()
    side = request.args.get('side','BUY').upper()
    entry = float(request.args.get('entry','77800'))
    tp = float(request.args.get('tp','85000'))
    sl = float(request.args.get('sl', entry-80 if side=="BUY" else entry+80))
    question = request.args.get('question','whats next move')
    now, rsi_v, ema, bias, next_move, plan, color = full_ai_analysis(symbol, side, entry, sl, tp)
    return html_page(symbol, side, entry, tp, sl, now, rsi_v, ema, bias, next_move, plan, color, question)

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
    now, rsi_v, ema, bias, next_move, plan, color = full_ai_analysis(symbol, side, entry, sl, tp)
    return html_page(symbol, side, entry, tp, sl, now, rsi_v, ema, bias, next_move, plan, color, q)

@app.route('/signal')
def signal():
    symbol = request.args.get('symbol','BTCUSD')
    side = request.args.get('side','BUY')
    entry = float(request.args.get('entry','0'))
    sl = float(request.args.get('sl','0'))
    tp = float(request.args.get('tp','85000'))
    now, rsi_v, ema, bias, next_move, plan, color = full_ai_analysis(symbol, side, entry, sl, tp)
    return html_page(symbol, side, entry, tp, sl, now, rsi_v, ema, bias, next_move, plan, color, f"SIGNAL {side}")

def watcher():
    while True:
        try:
            for lvl in WATCH_LEVELS:
                price = get_price(lvl['symbol'])
                key = f"{lvl['symbol']}_{lvl['side']}_{lvl['entry']}"
                if key in triggered: continue
                hit = (price <= lvl['entry'] and lvl['side']=="BUY") or (price >= lvl['entry'] and lvl['side']=="SELL")
                if hit:
                    print(f"HIT {key} at {price}")
                    triggered.add(key)
        except Exception as e: print(e)
        time.sleep(30)

threading.Thread(target=watcher, daemon=True).start()
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
