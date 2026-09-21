import os, requests
from flask import Flask, request

app = Flask(__name__)

PHONE = "447774862414"
APIKEY = "1511193"
AUTH_KEY = "Bongani_ireland2026"

def get_real_price(symbol):
    # Try Binance first (most reliable on Render)
    try:
        mapping = {"BTCUSD":"BTCUSDT", "GOLD":"PAXGUSDT", "XAUUSD":"PAXGUSDT"}
        bin_sym = mapping.get(symbol, "BTCUSDT")
        r = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={bin_sym}", timeout=5).json()
        price = float(r['price'])
        if "GOLD" in symbol or "XAU" in symbol:
            return price # PAXG = Gold price
        return price
    except:
        pass
    # Fallback
    try:
        r = requests.get(f"https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,pax-gold&vs_currencies=usd", timeout=5).json()
        if "BTC" in symbol: return r['bitcoin']['usd']
        else: return r['pax-gold']['usd']
    except:
        return None

def calc_levels(price, side):
    if not price: return price, price, price
    # Wide SL = 2% for BTC, 1.5% for Gold, TP1=1%, TP2=2%
    if side == "BUY":
        sl = price * 0.98
        tp1 = price * 1.01
        tp2 = price * 1.02
    else:
        sl = price * 1.02
        tp1 = price * 0.99
        tp2 = price * 0.98
    return round(sl,2), round(tp1,2), round(tp2,2)

def send_wa(msg):
    url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE}&text={requests.utils.quote(msg)}&apikey={APIKEY}"
    return requests.get(url, timeout=10).text

@app.route("/")
def home():
    if request.args.get("key")!= AUTH_KEY:
        return "Add?key=Bongani_ireland2026", 401

    btc = get_real_price("BTCUSD")
    gold = get_real_price("GOLD")
    btc_sl, btc_tp1, btc_tp2 = calc_levels(btc, "BUY")
    gold_sl, gold_tp1, gold_tp2 = calc_levels(gold, "SELL")

    # Simple page to see live prices
    return f"""
    <h1>✅ LIVE - TO: {PHONE}</h1>
    <h2>REAL MARKET NOW: BTC ${btc} | GOLD ${gold}</h2>
    <p>GOLD SELL SL {gold_sl} TP1 {gold_tp1} TP2 {gold_tp2}</p>
    <p>BTC BUY SL {btc_sl} TP1 {btc_tp1} TP2 {btc_tp2}</p>
    <p><a href="/?key={AUTH_KEY}&sendbtc=1">Send BTC signal now</a></p>
    """

@app.route("/test")
def test():
    return send_wa("RENDER LIVE TEST - Real BTC now ~85936")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
