from flask import Flask, make_response, request
import requests, os, time

app = Flask(__name__)

WHATSAPP_PHONE = "447774862414"
WHATSAPP_APIKEY = "1511193"
ALERT_FILE = "/tmp/alert_price.txt"
LAST_ALERT_FILE = "/tmp/last_alert.txt"
DEFAULT_ALERT = 4340.0

def get_gold():
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=8).json()
        p = float(r['price'])
        if 3000 < p < 5000: return p
    except: pass
    try:
        h={'User-Agent':'Mozilla/5.0'}
        r=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X", headers=h, timeout=8).json()
        return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
    except: return 4361.0

def send_whatsapp(text):
    try:
        url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={requests.utils.quote(text)}&apikey={WHATSAPP_APIKEY}"
        requests.get(url, timeout=10)
        return True
    except: return False

def get_alert():
    try:
        if os.path.exists(ALERT_FILE):
            return float(open(ALERT_FILE).read().strip())
    except: pass
    return DEFAULT_ALERT

def set_alert(p):
    try: open(ALERT_FILE,'w').write(str(p))
    except: pass

def should_send_alert():
    try:
        if os.path.exists(LAST_ALERT_FILE):
            last = float(open(LAST_ALERT_FILE).read())
            if time.time() - last < 600: return False
    except: pass
    return True

def mark_alert_sent():
    try: open(LAST_ALERT_FILE,'w').write(str(time.time()))
    except: pass

def check_and_alert():
    gold = round(get_gold(),2)
    alert = get_alert()
    if gold <= alert and should_send_alert():
        msg = f"🚨 GOLD Dips Below {alert}\nNow: {gold}\nSELL\nSL: {gold+5.5}\nTP1: {gold-4} | TP2: {gold-9}\nBot: XM SPOT LIVE"
        send_whatsapp(msg)
        mark_alert_sent()
        return True, gold, alert
    return False, gold, alert

@app.route('/')
def home():
    new_alert = request.args.get('alert')
    if new_alert:
        try: set_alert(float(new_alert))
        except: pass
    # Also check on every visit
    sent, gold, alert = check_and_alert()
    html = f"""
    <html><head><meta name="viewport" content="width=device-width, initial-scale=1">
    <meta http-equiv="refresh" content="60"></head>
    <body style="background:#0a0a0a;color:white;font-family:Arial;padding:12px;">
    <div style="background:#00c853;padding:10px;border-radius:8px;text-align:center;">✅ LIVE - Auto WhatsApp ON - TO: {WHATSAPP_PHONE}</div>
    <div style="background:#1e1e1e;border:2px solid #ffca28;padding:12px;margin-top:12px;border-radius:10px;">
    <b style="color:#ffca28;">🔔 AUTO ALERT: {alert}</b> | Gold: {gold}<br>
    <input id="p" type="number" value="{alert}" style="flex:1;padding:10px;border-radius:8px;border:none;width:60%;">
    <button onclick="location.href='/?alert='+document.getElementById('p').value" style="padding:10px;background:#ffca28;border:none;border-radius:8px;font-weight:bold;">SET</button>
    <br><br><a href="/test"><button style="padding:10px;background:#25D366;color:white;border:none;border-radius:8px;width:100%;">📱 TEST WHATSAPP NOW</button></a>
    <small style="color:#aaa;">UptimeRobot pings /check every 5 min to check & send WhatsApp even at 2am</small>
    </div>
    <div style="background:#1e1e1e;padding:12px;margin-top:12px;border-radius:8px;border-left:5px solid #00e676;">
    GOLD ENTRY <b style="font-size:24px;">{gold}</b><br>Watching for Dips Below {alert}
    </div>
    <p style="text-align:center;color:#777;font-size:11px;">APIKEY 1511193 Active - Bot: whatsapp-signal-bot</p>
    </body></html>"""
    resp = make_response(html)
    resp.headers['Cache-Control']='no-store'
    return resp

@app.route('/test')
def test():
    g=round(get_gold(),2)
    send_whatsapp(f"✅ TEST OK - Gold {g} - Alert {get_alert()} - Bot whatsapp-signal-bot LIVE")
    return f"Test WhatsApp sent to {WHATSAPP_PHONE}! Gold {g}"

@app.route('/check')
def check():
    # This is what UptimeRobot calls every 5 min
    sent, gold, alert = check_and_alert()
    return f"OK Gold={gold} Alert={alert} Sent={sent} Phone={WHATSAPP_PHONE}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",10000)))
