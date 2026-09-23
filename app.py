from flask import Flask, make_response, request
import requests, os, threading, time

app = Flask(__name__)

# YOUR WORKING WHATSAPP DETAILS
WHATSAPP_PHONE = "447774862414"
WHATSAPP_APIKEY = "1511193"
ALERT_PRICE_FILE = "/tmp/gold_alert.txt"
DEFAULT_ALERT = 4340.0

def get_gold_spot():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=8).json()
        price = float(r['price'])
        if 3000 < price < 5000: return price
    except: pass
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        r = requests.get("https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X", headers=headers, timeout=8).json()
        return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
    except: return 4361.0

def send_whatsapp(text):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={requests.utils.quote(text)}&apikey={WHATSAPP_APIKEY}"
        requests.get(url, timeout=10)
        print("WhatsApp sent:", text)
        return True
    except as e:
        print("WhatsApp failed:", e)
        return False

def get_alert_price():
    try:
        if os.path.exists(ALERT_PRICE_FILE):
            with open(ALERT_PRICE_FILE, 'r') as f:
                return float(f.read().strip())
    except: pass
    return DEFAULT_ALERT

def set_alert_price(price):
    try:
        with open(ALERT_PRICE_FILE, 'w') as f:
            f.write(str(price))
    except: pass

# BACKGROUND CHECKER - runs every 60 sec
def background_checker():
    last_alert_sent = 0
    while True:
        try:
            gold = round(get_gold_spot(), 2)
            alert_price = get_alert_price()
            # If gold dips below alert
            if gold <= alert_price and (time.time() - last_alert_sent) > 600: # 10 min cooldown
                msg = f"🚨 GOLD Dips Below {alert_price} USDT\nNow: {gold}\nSignal: SELL\nSL: {gold+5.5} (55 pips)\nTP1: {gold-4} | TP2: {gold-9}\nTime: {time.strftime('%H:%M UTC')}\n\nBot: XM SPOT LIVE"
                send_whatsapp(msg)
                last_alert_sent = time.time()
            time.sleep(60)
        except:
            time.sleep(60)

threading.Thread(target=background_checker, daemon=True).start()

@app.route('/')
def home():
    # Allow setting alert via?alert=4340
    new_alert = request.args.get('alert')
    if new_alert:
        try:
            set_alert_price(float(new_alert))
        except: pass

    gold_price = round(get_gold_spot(),2)
    alert_price = get_alert_price()

    html = f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="30">
    </head>
    <body style="background:#0a0a0a;color:white;font-family:Arial;padding:12px;">
    <div style="background:#00c853;padding:10px;border-radius:8px;text-align:center;font-weight:bold;">✅ LIVE - Auto WhatsApp Alert ON - TO: {WHATSAPP_PHONE}</div>

    <div style="background:#1e1e1e;border:2px solid #ffca28;padding:12px;margin-top:12px;border-radius:10px;">
    <b style="color:#ffca28;">🔔 AUTO WHATSAPP ALERT ACTIVE</b><br>
    <small>Current Alert: <b style="color:#00e676;font-size:16px;">{alert_price}</b> | Gold Now: {gold_price}</small><br>
    <div style="display:flex;gap:6px;margin-top:8px;">
    <input id="p" type="number" value="{alert_price}" style="flex:1;padding:10px;border-radius:8px;border:none;">
    <button onclick="location.href='/?alert='+document.getElementById('p').value" style="padding:10px 16px;background:#ffca28;color:black;border:none;border-radius:8px;font-weight:bold;">SET & SAVE</button>
    </div>
    <small style="color:#aaa;">Bot will WhatsApp Bongani when Gold hits this price, even at 2am. 10 min cooldown.</small>
    <br><button onclick="fetch('/test').then(()=>alert('Test WhatsApp sent! Check +34 bot'))" style="margin-top:8px;padding:8px 12px;background:#25D366;color:white;border:none;border-radius:6px;">📱 TEST WHATSAPP NOW</button>
    </div>

    <div style="background:#1e1e1e;padding:12px;margin-top:12px;border-radius:8px;border-left:5px solid #00e676;">
    GOLD micro • BUY/SELL based on live • <b style="font-size:26px;">ENTRY {gold_price}</b><br>
    Watching for Dips Below {alert_price} → Auto WhatsApp
    </div>

    <button onclick="location.reload(true)" style="width:100%;margin-top:14px;padding:16px;background:#2962ff;color:white;border:none;border-radius:10px;font-size:18px;font-weight:bold;">🔄 REFRESH NOW</button>
    <p style="text-align:center;color:#777;font-size:11px;margin-top:10px;">To stop sleeping: Add this link to UptimeRobot (ping every 5 mins)<br>Auto WhatsApp uses APIKEY 1511193</p>
    </body></html>
    """
    resp = make_response(html)
    resp.headers['Cache-Control'] = 'no-store'
    return resp

@app.route('/test')
def test():
    send_whatsapp(f"✅ TEST OK - GOLD Bot is AWAKE - Gold now {round(get_gold_spot(),2)} - Alert set for {get_alert_price()}")
    return "Test sent"

@app.route('/check')
def check():
    # For UptimeRobot to ping and trigger check
    gold = round(get_gold_spot(),2)
    return f"OK Gold {gold} Alert {get_alert_price()}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
