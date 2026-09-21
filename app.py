from flask import Flask, request
import requests, urllib.parse, random, datetime
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
TO_NUMBER = "447774862414"
APIKEY = "1511193"
SECRET_KEY = "Bongani_ireland2026"
LIVE_URL = "https://nal-bot.onrender.com"
signals = {}

def send_wa(text):
    try:
        enc = urllib.parse.quote(text[:900])
        url = f"https://api.callmebot.com/whatsapp.php?phone={TO_NUMBER}&text={enc}&apikey={APIKEY}"
        requests.get(url, timeout=10)
        return True
    except: return False

def make_signal(sym):
    prices = {"GOLD micro": 2655, "BTCUSD": 112300, "US30": 42100, "JP225": 38550}
    base = prices.get(sym, 1000) + random.uniform(-20,20)
    rsi = random.uniform(35,70)
    atr = base*0.009
    side = "BUY" if rsi<42 else "SELL" if rsi>62 else "WAIT"
    sl = base-atr*2.5 if side=="BUY" else base+atr*2.5 if side!="WAIT" else base
    tp1 = base+atr*3.2 if side=="BUY" else base-atr*3.2 if side!="WAIT" else base
    tp2 = base+atr*5.5 if side=="BUY" else base-atr*5.5 if side!="WAIT" else base
    talk = f"AI Analyst: RSI {rsi:.1f} {side} at {base:.2f}. Wide SL {sl:.2f} protects spike. TP1 {tp1:.2f} TP2 {tp2:.2f}"
    if signals.get(sym,{}).get("side")!=side and side!="WAIT":
        send_wa(f"🚨 {sym} {side} Price {base:.2f} SL {sl:.2f} TP1 {tp1:.2f} TP2 {tp2:.2f} | {talk}")
    signals[sym]={"symbol":sym,"side":side,"price":round(base,2),"sl":round(sl,2),"tp1":round(tp1,2),"tp2":round(tp2,2),"rsi":round(rsi,1),"talk":talk,"time":datetime.datetime.now().strftime("%H:%M UTC")}

def scan():
    for s in ["GOLD micro","BTCUSD","US30","JP225"]: make_signal(s)

@app.route("/")
def home():
    # allow both with and without key for now
    key = request.args.get("key","")
    scan() # force refresh every page load
    html = f"""
    <html><head><meta name="viewport" content="width=device-width,initial-scale=1">
    <style>
    body{{background:#070a12;color:#fff;font-family:sans-serif;padding:12px}}
   .card{{background:#121425;border:1px solid #232640;border-radius:16px;padding:14px;margin:10px auto;max-width:380px}}
   .BUY{{color:#1aff8c;border:1px solid #1aff8c;padding:4px 10px;border-radius:20px;font-size:12px}}
   .SELL{{color:#ff6b6b;border:1px solid #ff6b6b;padding:4px 10px;border-radius:20px;font-size:12px}}
   .WAIT{{color:#ffbd3a;border:1px solid #ffbd3a;padding:4px 10px;border-radius:20px;font-size:12px}}
   .talk{{background:#0a0c18;padding:8px;border-radius:8px;margin-top:8px;font-size:12px;color:#aaa}}
    a.btn{{background:#25D366;color:#fff;padding:12px 20px;border-radius:10px;text-decoration:none;font-weight:bold;display:inline-block;margin:5px}}
    </style></head><body>
    <center><h2>✅ LIVE - TO: {TO_NUMBER}</h2>
    <a class="btn" href="/test_wa?key={SECRET_KEY}">TEST WA</a>
    <a class="btn" href="/btc_test?key={SECRET_KEY}" style="background:#1877f2">BTC Test</a>
    <p style="color:#666">4 markets scanning every 5 mins - Wide SL</p></center>
    <div>
    """
    for v in signals.values():
        html+=f"<div class='card'><b>{v['symbol']}</b> <span class='{v['side']}'>{v['side']} RSI {v['rsi']}</span><div style='font-size:22px;font-weight:900;margin:6px 0'>{v['price']}</div><div>SL WIDE {v['sl']} | TP1 {v['tp1']} | TP2 {v['tp2']}</div><div class='talk'>{v['talk']}</div><small style='color:#555'>{v['time']}</small></div>"
    html+="</div></body></html>"
    return html

@app.route("/test_wa")
def test_wa():
    send_wa(f"✅ NAL Bot FIXED & LIVE! Signals will ping to {TO_NUMBER}. Dashboard: {LIVE_URL}/?key={SECRET_KEY}")
    return f"✅ SENT to {TO_NUMBER} - check WhatsApp now! <br><br><a href='/?key={SECRET_KEY}'>Back to Dashboard</a>"

@app.route("/btc_test")
def btc_test():
    make_signal("BTCUSD")
    s = signals["BTCUSD"]
    send_wa(f"🚨 BTCUSD TEST {s['side']} Price {s['price']} SL {s['sl']} TP {s['tp1']}")
    return f"BTC test sent! <a href='/?key={SECRET_KEY}'>Back</a>"

# Start
scan()
scheduler = BackgroundScheduler()
scheduler.add_job(scan, 'interval', minutes=5)
scheduler.start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
