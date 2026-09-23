from flask import Flask, request, render_template_string
import requests
from datetime import datetime

app = Flask(__name__)

SITE_KEY = "Bongani_ireland2026"
PHONE = "447774862414"
APIKEY = "1511193"
GOLD_ALERT = 4340.0

signals_store = {}
prices_store = {"GOLD": 4286.1, "BTCUSD": 85852.0, "JP225": 64969.0, "US30": 51863.0}

def ok():
    return request.args.get('key') == SITE_KEY

def get_prices():
    p = {}
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
        p["GOLD"] = float(r['price'])
        prices_store["GOLD"] = p["GOLD"]
    except:
        p["GOLD"] = prices_store["GOLD"]
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5).json()
        p["BTCUSD"] = float(r['bitcoin']['usd'])
        prices_store["BTCUSD"] = p["BTCUSD"]
    except:
        p["BTCUSD"] = prices_store["BTCUSD"]
    import random
    for s in ["JP225","US30"]:
        p[s] = round(prices_store[s] + random.uniform(-30,30),1)
        prices_store[s] = p[s]
    return p

def get_signal(sym, price):
    if sym not in signals_store:
        side = "SELL" if sym=="GOLD" and price<=GOLD_ALERT else "BUY"
        signals_store[sym] = {"side":side,"entry":price}
        return side, f"START {side} at {price} waiting 200 pips", False
    entry = signals_store[sym]["entry"]
    old = signals_store[sym]["side"]
    move = price - entry
    pips = abs(move)/0.1 if sym=="GOLD" else abs(move)
    need = 20.0 if sym=="GOLD" else 200.0
    if abs(move) >= need:
        new = "BUY" if move>0 else "SELL"
        signals_store[sym] = {"side":new,"entry":price}
        return new, f"{move:+.1f} ({pips:.0f} pips) >200pips {old}->{new} CONFIRMED", True
    return old, f"{move:+.1f} ({pips:.0f} pips) from entry {entry} Holding {old} until {need} - No flip", False

def send_wa(m):
    try:
        requests.get(f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={m}&apikey={APIKEY}", timeout=10)
        return True
    except:
        return False

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="refresh" content="30">
<style>body{background:#111;color:#fff;font-family:Arial;padding:15px}
.card{background:#1e1e1e;border-radius:12px;padding:14px;margin:12px 0;border-left:5px solid #0f0}
.badge{padding:4px 10px;border-radius:6px;font-weight:bold}
.buy{background:#00ff88;color:#000}.sell{background:#ff4444;color:#fff}
.btn{display:block;padding:13px;border-radius:10px;text-align:center;text-decoration:none;font-weight:bold;margin:10px 0}
.green{background:#00ff88;color:#000}.blue{background:#3b82f6;color:#fff}
.small{font-size:11px;color:#aaa}
</style></head><body>
<h2>📊 200 PIPS LIVE - Bongani_ireland2026</h2>
<p>Alert {{alert}} | Now {{gold}} | {{time}} | Auto 30s</p>
<a class="btn blue" href="/?key={{key}}">🔄 REFRESH NOW</a>
{% for s in sigs %}
<div class="card" style="border-left-color:{{s.col}}">
<b>{{s.sym}} XM</b> <span class="badge {{s.cls}}">{{s.side}}</span> {{s.price}}
<div class="small">{{s.txt}}</div>
<div style="margin-top:8px;font-size:13px">ENTRY {{s.price}} | SL {{s.sl}}<br>TP1 {{s.tp1}} (1:3) | TP2 {{s.tp2}} (1:5) | TP3 {{s.tp3}} (1:8)</div>
</div>
{% endfor %}
<a class="btn green" href="/test?key={{key}}">📱 TEST WHATSAPP</a>
<a class="btn blue" href="/?key={{key}}">🔄 REFRESH PRICES</a>
</body></html>
"""

@app.route('/')
def home():
    if not ok(): return "need key",403
    pr = get_prices()
    sigs=[]
    for sym,price in pr.items():
        side,txt,is200 = get_signal(sym,price)
        d={"GOLD":5.5,"BTCUSD":120,"JP225":85,"US30":90}[sym]
        if side=="BUY":
            sl=price-d; tp1=price+d*3; tp2=price+d*5; tp3=price+d*8
        else:
            sl=price+d; tp1=price-d*3; tp2=price-d*5; tp3=price-d*8
        sigs.append({"sym":sym,"price":price,"side":side,"cls":"buy" if side=="BUY" else "sell","col":"#00ff88" if side=="BUY" else "#ff4444","txt":txt,"sl":round(sl,2),"tp1":round(tp1,2),"tp2":round(tp2,2),"tp3":round(tp3,2)})
    return render_template_string(HTML,sigs=sigs,alert=GOLD_ALERT,gold=pr.get("GOLD"),time=datetime.now().strftime("%H:%M:%S"),key=SITE_KEY)

@app.route('/check')
def chk():
    if not ok(): return "need key",403
    pr=get_prices()
    return f"OK {pr}"

@app.route('/test')
def tst():
    if not ok(): return "need key",403
    send_wa(f"Bot v4 LIVE REFRESH OK {datetime.now()}")
    return "sent"

if __name__=='__main__':
    app.run(host='0.0.0.0',port=10000)
