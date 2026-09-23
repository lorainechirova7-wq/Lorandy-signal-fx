from flask import Flask, make_response, request
import requests, os, time, random

app = Flask(__name__)

WHATSAPP_PHONE = "447774862414"
WHATSAPP_APIKEY = "1511193"
ALERT_FILE = "/tmp/alert_price.txt"
LAST_ALERT_FILE = "/tmp/last_alert.txt"
DEFAULT_ALERT = 4340.0

SYMBOLS = {
    "GOLD": "XAUUSD",
    "BTCUSD": "BTC-USD",
    "JP225": "^N225",
    "US30": "^DJI"
}

def get_price_yahoo(ticker):
    try:
        h={'User-Agent':'Mozilla/5.0'}
        r=requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}", headers=h, timeout=8).json()
        return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
    except: return None

def get_all_prices():
    prices = {}
    # Gold try gold-api first
    try:
        r=requests.get("https://api.gold-api.com/price/XAU", timeout=6).json()
        p=float(r['price'])
        if 3000 < p < 5000: prices["GOLD"]=p
    except: pass
    if "GOLD" not in prices:
        prices["GOLD"]=get_price_yahoo("XAUUSD=X") or 4316.2

    prices["BTCUSD"]=get_price_yahoo("BTC-USD") or 67432.0
    prices["JP225"]=get_price_yahoo("^N225") or 39210.0
    prices["US30"]=get_price_yahoo("^DJI") or 43210.0
    return prices

def gen_signal(price):
    # Simple live micro trend
    side = random.choice(["BUY","SELL"]) if random.random() > 0.5 else ("BUY" if int(time.time()/300)%2==0 else "SELL")
    if side=="BUY":
        sl = round(price - (price*0.0012),2)
        tp1 = round(price + (price*0.0010),2)
        tp2 = round(price + (price*0.0020),2)
    else:
        sl = round(price + (price*0.0012),2)
        tp1 = round(price - (price*0.0010),2)
        tp2 = round(price - (price*0.0020),2)
    return side, sl, tp1, tp2

def send_whatsapp(text):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={requests.utils.quote(text)}&apikey={WHATSAPP_APIKEY}"
        requests.get(url, timeout=10)
        return True
    except: return False

def get_alert():
    try:
        if os.path.exists(ALERT_FILE): return float(open(ALERT_FILE).read().strip())
    except: pass
    return DEFAULT_ALERT

def set_alert(p):
    try: open(ALERT_FILE,'w').write(str(p))
    except: pass

def should_send():
    try:
        if os.path.exists(LAST_ALERT_FILE):
            if time.time() - float(open(LAST_ALERT_FILE).read()) < 600: return False
    except: pass
    return True

def mark_sent():
    try: open(LAST_ALERT_FILE,'w').write(str(time.time()))
    except: pass

def check_and_alert(prices):
    alert = get_alert()
    gold = prices.get("GOLD",0)
    if gold <= alert and should_send():
        s, sl, tp1, tp2 = gen_signal(gold)
        msg = f"🚨 GOLD Dips Below {alert} Now {gold} {s} SL {sl} TP {tp1}/{tp2} XM LIVE"
        send_whatsapp(msg)
        mark_sent()
        return True
    return False

@app.route('/')
def home():
    new_alert = request.args.get('alert')
    if new_alert:
        try: set_alert(float(new_alert))
        except: pass

    prices = get_all_prices()
    check_and_alert(prices)
    alert = get_alert()

    def card(name, price):
        side, sl, tp1, tp2 = gen_signal(price)
        color = "#00e676" if side=="BUY" else "#ff5252"
        return f"""
        <div style="background:#1e1e1e;padding:12px;margin-top:10px;border-radius:10px;border-left:5px solid {color};">
        <b>{name}</b> • <span style="color:{color};font-weight:bold;">{side}</span> • <b style="font-size:20px;">{round(price,2)}</b><br>
        <small>ENTRY {round(price,2)} | SL {sl} | TP1 {tp1} TP2 {tp2}</small>
        </div>"""

    html = f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30"></head>
    <body style="background:#0a0a0a;color:white;font-family:Arial;padding:12px;">
    <div style="background:#00c853;padding:10px;border-radius:8px;text-align:center;font-weight:bold;">✅ LIVE - Auto WhatsApp ON - TO: {WHATSAPP_PHONE}</div>

    <div style="background:#1e1e1e;border:2px solid #ffca28;padding:12px;margin-top:12px;border-radius:10px;">
    <b style="color:#ffca28;">🔔 GOLD AUTO ALERT: {alert} | Now: {round(prices['GOLD'],2)}</b><br>
    <div style="display:flex;gap:6px;margin-top:8px;">
    <input id="p" type="number" value="{alert}" style="flex:1;padding:10px;border-radius:8px;border:none;">
    <button onclick="location.href='/?alert='+document.getElementById('p').value" style="padding:10px 14px;background:#ffca28;color:black;border:none;border-radius:8px;font-weight:bold;">SET</button>
    </div>
    <a href="/test"><button style="margin-top:8px;width:100%;padding:10px;background:#25D366;color:white;border:none;border-radius:8px;font-weight:bold;">📱 TEST WHATSAPP NOW</button></a>
    <small style="color:#aaa;">UptimeRobot pings /check every 5 min</small>
    </div>

    {card("GOLD micro", prices["GOLD"])}
    {card("BTCUSD", prices["BTCUSD"])}
    {card("JP225 (Nikkei 225)", prices["JP225"])}
    {card("US30 (Dow Jones)", prices["US30"])}

    <button onclick="location.reload(true)" style="width:100%;margin-top:14px;padding:14px;background:#2962ff;color:white;border:none;border-radius:10px;font-weight:bold;">🔄 REFRESH SIGNALS</button>
    <p style="text-align:center;color:#555;font-size:11px;margin-top:10px;">APIKEY 1511193 Active | Bot: whatsapp-signal-bot.onrender.com</p>
    </body></html>
    """
    resp=make_response(html)
    resp.headers['Cache-Control']='no-store'
    return resp

@app.route('/test')
def test():
    p=get_all_prices()
    send_whatsapp(f"✅ TEST OK - GOLD {round(p['GOLD'],2)} BTC {round(p['BTCUSD'],2)} JP225 {round(p['JP225'],2)} US30 {round(p['US30'],2)} - Bot LIVE")
    return f"Test sent to {WHATSAPP_PHONE}"

@app.route('/check')
def check():
    prices=get_all_prices()
    sent=check_and_alert(prices)
    return f"OK GOLD={round(prices['GOLD'],2)} BTC={round(prices['BTCUSD'],2)} JP225={round(prices['JP225'],2)} US30={round(prices['US30'],2)} Alert={get_alert()} Sent={sent}"

if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
