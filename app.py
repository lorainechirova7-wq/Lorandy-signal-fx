from flask import Flask, request, render_template_string
import requests, yfinance as yf, random
from datetime import datetime

app = Flask(__name__)

# === YOUR REAL KEYS ===
SITE_KEY = "Bongani_ireland2026"
WHATSAPP_PHONE = "447774862414"
WHATSAPP_APIKEY = "1511193" # CallMeBot API key
GOLD_ALERT = 4340.0

# Store last signal to stop scalping BUY/SELL flip
last_signals = {}

# 200 PIPS DEFINITION (XM exact 2026)
PIPS_200 = {
    "GOLD": 20.0, # 200 pips = $20.0 (1 pip = $0.1)
    "BTCUSD": 200.0,
    "JP225": 200.0,
    "US30": 200.0
}

SL_DIST = {
    "GOLD": 5.5,
    "BTCUSD": 120.0,
    "JP225": 85.0,
    "US30": 90.0
}

def check_key():
    return request.args.get('key') == SITE_KEY

def get_all_prices():
    prices = {}
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
        prices["GOLD"] = float(r['price'])
    except:
        prices["GOLD"] = 4317.4
    try:
        prices["BTCUSD"] = float(yf.Ticker("BTC-USD").history(period="1d")['Close'].iloc[-1])
    except:
        prices["BTCUSD"] = 85852.0
    try:
        prices["JP225"] = float(yf.Ticker("^N225").history(period="1d")['Close'].iloc[-1])
    except:
        prices["JP225"] = 65018.0
    try:
        prices["US30"] = float(yf.Ticker("^DJI").history(period="1d")['Close'].iloc[-1])
    except:
        prices["US30"] = 51863.0
    return prices

def get_trend_200pips(symbol, yahoo_symbol, current_price):
    try:
        ticker = yf.Ticker(yahoo_symbol)
        hist = ticker.history(period="5d", interval="15m")
        if len(hist) < 20:
            hist = ticker.history(period="2d", interval="5m")

        old_price = hist['Close'].iloc[-48] if len(hist) > 48 else hist['Close'].iloc[0]
        move = current_price - old_price
        move_pips = abs(move) / 0.1 if symbol == "GOLD" else abs(move)
        threshold = PIPS_200[symbol]

        if abs(move) >= threshold:
            side = "BUY" if move > 0 else "SELL"
            reason = f"{move:+.1f} ({move_pips:.0f} pips) in 12H > 200pips {side} TREND"
            last_signals[symbol] = side
            return side, reason, True

        if symbol in last_signals:
            side = last_signals[symbol]
            reason = f"Only {move:+.1f} ({move_pips:.0f} pips) <200pips - KEEP {side} no scalping"
            return side, reason, False
        else:
            side = "BUY" if move >= 0 else "SELL"
            last_signals[symbol] = side
            reason = f"First signal {move:+.1f} -> {side}"
            return side, reason, False

    except:
        side = last_signals.get(symbol, random.choice(["BUY","SELL"]))
        return side, f"Keep {side} (data error)", False

def gen_signal(price, symbol, yahoo_symbol):
    side, analysis, is_200 = get_trend_200pips(symbol, yahoo_symbol, price)
    sl_dist = SL_DIST[symbol]
    if side == "BUY":
        sl = price - sl_dist
        tp1 = price + sl_dist*3
        tp2 = price + sl_dist*5
        tp3 = price + sl_dist*8
    else:
        sl = price + sl_dist
        tp1 = price - sl_dist*3
        tp2 = price - sl_dist*5
        tp3 = price - sl_dist*8
    return side, round(sl,2), round(tp1,2), round(tp2,2), round(tp3,2), analysis, is_200

def send_whatsapp(msg):
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={msg}&apikey={WHATSAPP_APIKEY}"
    try:
        requests.get(url, timeout=10)
        return True
    except:
        return False

HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Signal 200 PIPS - Bongani</title>
<style>
body{background:#0f0f0f;color:#fff;font-family:Arial;padding:15px}
.card{background:#1a1a1a;border-radius:12px;padding:15px;margin-bottom:12px;border-left:4px solid {{'red'}}}
.badge{padding:3px 8px;border-radius:5px;font-size:12px;font-weight:bold}
.buy{background:#00ff88;color:#000}.sell{background:#ff4444;color:#fff}
.small{font-size:11px;color:#9ca3af;margin-top:6px}
.strong{color:#00ff88;font-weight:bold}
</style></head><body>
<h2>📊 200 PIPS Bot - Bongani_ireland2026</h2>
<p>Gold Alert: {{alert}} | Now: {{gold_price}} | {{time}}</p>
{% for s in signals %}
<div class="card" style="border-left-color:{{s.color}}">
  <div><b>{{s.symbol}} XM exact</b> • <span class="badge {{s.side_class}}">{{s.side}}</span> • {{s.price}}</div>
  <div class="small">📈 {{s.analysis}}</div>
  {% if s.is_200 %}<div class="small strong">✅ 200+ PIPS CONFIRMED</div>
  {% else %}<div class="small">⏳ Waiting 200 pips - No scalping flip</div>{% endif %}
  <div style="margin-top:8px;font-size:13px;line-height:1.6">
    ENTRY {{s.price}} | SL {{s.sl}} (1R)<br>
    TP1 {{s.tp1}} (1:3) | TP2 {{s.tp2}} (1:5) | TP3 {{s.tp3}} (1:8)<br>
    RR: 1:3 / 1:5 / 1:8
  </div>
</div>
{% endfor %}
<a href="/test?key={{key}}" style="display:block;background:#00ff88;color:#000;text-align:center;padding:12px;border-radius:8px;text-decoration:none;margin-top:20px;font-weight:bold">TEST WHATSAPP NOW</a>
<p class="small">Bongani Link:?key={{key}} | /check?key={{key}} for UptimeRobot</p>
</body></html>
"""

@app.route('/')
def home():
    if not check_key(): return f"Need?key={SITE_KEY}", 403
    prices = get_all_prices()
    yahoo_map = {"GOLD":"GC=F","BTCUSD":"BTC-USD","JP225":"^N225","US30":"^DJI"}
    signals = []
    for sym, price in prices.items():
        side, sl, tp1, tp2, tp3, analysis, is_200 = gen_signal(price, sym, yahoo_map[sym])
        signals.append({
            "symbol": sym, "price": price, "side": side,
            "side_class": "buy" if side=="BUY" else "sell",
            "color": "#00ff88" if side=="BUY" else "#ff4444",
            "sl": sl, "tp1": tp1, "tp2": tp2, "tp3": tp3,
            "analysis": analysis, "is_200": is_200
        })
    return render_template_string(HTML, signals=signals, alert=GOLD_ALERT, gold_price=prices.get("GOLD"), time=datetime.now().strftime("%H:%M:%S"), key=SITE_KEY)

@app.route('/check')
def check():
    if not check_key(): return f"Need?key={SITE_KEY}", 403
    prices = get_all_prices()
    gold = prices.get("GOLD", 0)
    msg = ""
    if gold <= GOLD_ALERT and gold > 0:
        msg = f"🚨 GOLD 200 PIPS ALERT Below {GOLD_ALERT} Now {gold} SELL SL {gold+5.5} TP1 {gold-16.5} 1:3 TP2 {gold-27.5} 1:5 TP3 {gold-44} 1:8"
        send_whatsapp(msg)
    return f"OK Gold:{gold} Alert:{GOLD_ALERT} Msg:{msg} - 200pips no scalping"

@app.route('/test')
def test():
    if not check_key(): return f"Need?key={SITE_KEY}", 403
    ok = send_whatsapp(f"✅ 200 PIPS Bot Test OK {datetime.now().strftime('%H:%M:%S')} Bongani_ireland2026 RR 1:3 1:5 1:8")
    return f"WhatsApp sent: {ok} to {WHATSAPP_PHONE} with key {SITE_KEY}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
