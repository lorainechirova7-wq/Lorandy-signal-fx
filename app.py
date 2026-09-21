import os, requests, datetime
from flask import Flask, request, abort, render_template_string, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import yfinance as yf
import ta

app = Flask(__name__)
SECRET_KEY = "Bongani_ireland2026"
LIVE_URL = "https://whatsapp-signal-bot.onrender.com"
TO_NUMBER = "447774862414"
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN","")
WHATSAPP_PHONE_ID = os.environ.get("WHATSAPP_PHONE_ID","")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY","") # optional

MARKETS = {
    "GOLD micro": {"yf": "GC=F"},
    "JP225": {"yf": "^N225"},
    "BTCUSD": {"yf": "BTC-USD"},
    "US30": {"yf": "^DJI"}
}
signals = {}

def send_wa(text):
    if not WHATSAPP_TOKEN or not WHATSAPP_PHONE_ID: return False
    try:
        url = f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_ID}/messages"
        h = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
        p = {"messaging_product":"whatsapp","to":TO_NUMBER,"type":"text","text":{"body":text}}
        r = requests.post(url, json=p, headers=h, timeout=15)
        return r.status_code==200
    except: return False

def analyst_talk(symbol, side, price, rsi, atr, entry, sl, tp1, tp2, tp3, question=""):
    # 1. Try OpenAI if key exists
    if OPENAI_KEY:
        try:
            prompt = f"You are NAL, pro trader for {symbol}. Price {price}, RSI {rsi}, ATR {atr}, Side {side}, Entry {entry} SL {sl} TP1 {tp1} TP2 {tp2} TP3 {tp3}. User asks: {question}. Give 3-line analyst outlook: bias, next move after entry, plan with wide SL."
            r = requests.post("https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_KEY}","Content-Type":"application/json"},
                json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],"max_tokens":200}, timeout=20)
            return r.json()['choices'][0]['message']['content']
        except: pass

    # 2. FREE rule-based talking analyst (no key needed)
    if side=="BUY":
        return f"Bias: STRONG BUY on {symbol}. RSI {rsi} shows sellers exhausted at {price}. After tapping {entry}, expect a shallow retrace to {round(entry-atr*0.5,2)} for liquidity, then impulsive move to TP1 {tp1}. If momentum holds, extension to TP2 {tp2} and runner TP3 {tp3}. Wide SL at {sl} protects the wick - do not tighten. Question '{question}' -> answer: wait for bullish engulfing on 15m before entry."
    elif side=="SELL":
        return f"Bias: STRONG SELL on {symbol}. RSI {rsi} overbought, buyers trapped at {price}. After rejecting {entry}, expect bounce to {round(entry+atr*0.5,2)} then drop to TP1 {tp1}. Continuation to {tp2}, final {tp3} if breakdown holds. Wide SL {sl} above spike. For '{question}' -> look for bearish rejection wick at entry."
    else:
        return f"Bias: NEUTRAL/WAIT on {symbol}. RSI {rsi} mid-range at {price}. No clear zone yet. Market consolidating between {round(price-atr,2)} - {round(price+atr,2)}. For your question '{question}': wait for RSI <40 or >66 to form new BUY/SELL zone. Bot scanning every 8 mins."

def analyze(k, yf_sym):
    try:
        df = yf.download(yf_sym, period="7d", interval="1h", progress=False)
        close, high, low = df['Close'], df['High'], df['Low']
        price = float(close.iloc[-1])
        rsi = float(ta.momentum.RSIIndicator(close).rsi().iloc[-1])
        atr = float(ta.volatility.AverageTrueRange(high, low, close).average_true_range().iloc[-1])
        sl_dist = atr*2.5
        tp1, tp2, tp3 = atr*3.2, atr*5.5, atr*8.5
        prev = signals.get(k, {}).get("side","WAIT")
        side = "BUY" if rsi<40 else "SELL" if rsi>66 else "WAIT"
        entry = price
        sl = price-sl_dist if side!="SELL" else price+sl_dist
        t1 = price+tp1 if side!="SELL" else price-tp1
        t2 = price+tp2 if side!="SELL" else price-tp2
        t3 = price+tp3 if side!="SELL" else price-tp3
        talk = analyst_talk(k, side, price, round(rsi,1), round(atr,2), round(entry,2), round(sl,2), round(t1,2), round(t2,2), round(t3,2), "auto scan")

        if side in ["BUY","SELL"] and prev!=side:
            send_wa(f"🚨 {k} {side} AI ANALYST 🚨\nPrice {price}\nEntry {entry:.2f}\nWide SL {sl:.2f}\nTPs {t1:.2f} / {t2:.2f} / {t3:.2f}\n\n{talk}\n\nDashboard: {LIVE_URL}/?key={SECRET_KEY}")

        signals[k] = {"symbol":k,"side":side,"price":round(price,2),"entry":round(entry,2),"sl":round(sl,2),"tp1":round(t1,2),"tp2":round(t2,2),"tp3":round(t3,2),"rsi":round(rsi,1),"atr":round(atr,2),"talk":talk,"time":datetime.datetime.now().strftime("%H:%M UTC")}
    except Exception as e: print(e)

def scan_all():
    for k,v in MARKETS.items(): analyze(k,v["yf"])
    try: requests.get(f"{LIVE_URL}/?key={SECRET_KEY}", timeout=8)
    except: pass

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="refresh" content="180">
<style>body{background:#070a12;color:#eee;font-family:Inter,sans-serif;padding:14px}.head{text-align:center}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:16px;max-width:1200px;margin:auto}.card{background:#121425;border:1px solid #232640;border-radius:18px;padding:16px}.badge{padding:5px 12px;border-radius:20px;font-weight:800;font-size:11px}.BUY{background:#0b2d1e;color:#1aff8c;border:1px solid #1aff8c}.SELL{background:#2d1212;color:#ff6b6b;border:1px solid #ff6b6b}.WAIT{background:#2a2310;color:#ffbd3a;border:1px solid #ffbd3a}.price{font-size:24px;font-weight:900}.talk{background:#0a0c18;padding:12px;border-radius:12px;color:#c8ccea;font-size:13px;line-height:1.5;margin-top:10px;white-space:pre-wrap}.box{background:#0d0f1f;border:1px solid #232640;border-radius:10px;padding:6px;text-align:center}.askbox{max-width:600px;margin:20px auto;background:#15172a;padding:14px;border-radius:14px;border:1px solid #232640}input{width:100%;padding:14px;border-radius:10px;border:none;background:#0d0f1f;color:#fff;margin-top:8px}</style>
</head><body>
<div class="head"><h2>🤖 NAL AI ANALYST - BONGANI</h2><p style="color:#666">Talking AI • Wide SL • WhatsApp to {{num}} • Live</p>
<div class="askbox"><form action="/ask"><input name="q" placeholder="Ask: Gold after 4300? BTC next after 112k?" required><input type="hidden" name="key" value="{{key}}"><input type="submit" value="Ask AI Analyst" style="background:#6c5cff;color:#fff;font-weight:800"></form></div></div>
<div class="grid">{% for s in signals.values() %}
<div class="card"><div style="display:flex;justify-content:space-between"><b>{{s.symbol}}</b><span class="badge {{s.side}}">{{s.side}} RSI {{s.rsi}}</span></div><div class="price">{{s.price}}</div>
<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;margin:8px 0"><div class="box"><small>SL WIDE</small><br><b style="color:#ff6b6b">{{s.sl}}</b></div><div class="box"><small>TP1</small><br><b style="color:#1aff8c">{{s.tp1}}</b></div><div class="box"><small>TP2</small><br><b style="color:#1aff8c">{{s.tp2}}</b></div></div>
<div class="talk">{{s.talk}}</div><small style="color:#555">{{s.time}} • ATR {{s.atr}}</small></div>{% endfor %}</div>
</body></html>
"""

@app.route("/")
def home():
    if request.args.get("key")!=SECRET_KEY: return "401 Private use?key=Bongani_ireland2026",401
    return render_template_string(HTML, signals=signals, num=TO_NUMBER, key=SECRET_KEY)

@app.route("/ask")
def ask():
    if request.args.get("key")!=SECRET_KEY: abort(401)
    q = request.args.get("q","whats next?")
    # find symbol from question
    sym = "BTCUSD"
    if "gold" in q.lower() or "xau" in q.lower() or "mgc" in q.lower(): sym="GOLD micro"
    elif "jp" in q.lower() or "nikkei" in q.lower() or "225" in q: sym="JP225"
    elif "us30" in q.lower() or "dow" in q.lower() or "30" in q: sym="US30"
    s = signals.get(sym, list(signals.values())[0] if signals else None)
    if not s: return "Bot starting, wait 1 min <a href='/?key="+SECRET_KEY+"'>back</a>"
    talk = analyst_talk(sym, s['side'], s['price'], s['rsi'], s['atr'], s['entry'], s['sl'], s['tp1'], s['tp2'], s['tp3'], q)
    return f"<body style='background:#070a12;color:#fff;font-family:sans-serif;padding:20px'><h3>Q: {q}</h3><div style='background:#121425;padding:16px;border-radius:14px;border:1px solid #232640'>{talk}</div><br><a href='/?key={SECRET_KEY}' style='color:#6c5cff'>←
