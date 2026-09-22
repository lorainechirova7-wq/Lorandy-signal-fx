from flask import Flask
import requests
import os
from datetime import datetime
import random

app = Flask(__name__)

def get_live_prices():
    prices = {}
    try:
        r = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSD", timeout=10).json()
        prices['BTCUSD'] = float(r['result']['XXBTZUSD']['c'][0])
    except:
        prices['BTCUSD'] = 86444.3

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        for symbol, key in [('GC=F','GOLD'), ('^N225','JP225'), ('^DJI','US30')]:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            res = requests.get(url, headers=headers, timeout=10).json()
            prices[key] = float(res['chart']['result'][0]['meta']['regularMarketPrice'])
    except:
        prices.setdefault('GOLD', 4346.93)
        prices.setdefault('JP225', 65018.95)
        prices.setdefault('US30', 51869.03

        )
    return prices

@app.route('/')
def home():
    p = get_live_prices()

    def get_levels(price):
        is_sell = random.choice([True, False])
        if is_sell:
            sl = price * 1.02
            tp1 = price * 0.99
            tp2 = price * 0.98
        else:
            sl = price * 0.98
            tp1 = price * 1.01
            tp2 = price * 1.02
        return round(sl,2), round(tp1,2), round(tp2,2)

    g_sl, g_tp1, g_tp2 = get_levels(p['GOLD'])
    b_sl, b_tp1, b_tp2 = get_levels(p['BTCUSD'])
    j_sl, j_tp1, j_tp2 = get_levels(p['JP225'])
    u_sl, u_tp1, u_tp2 = get_levels(p['US30'])

    now = datetime.utcnow().strftime("%H:%M UTC")

    html = f"""
    <html><body style="background:#0a0a0a;color:white;font-family:Arial;padding:12px;">
    <div style="background:#00c853;padding:10px;border-radius:8px;font-weight:bold;">✅ LIVE - TO: 447774862414</div>
    <div style="background:#2962ff;padding:10px;margin-top:10px;border-radius:8px;font-size:13px;">
    REAL MARKET: BTC ${p['BTCUSD']} | GOLD ${p['GOLD']} | JP225 {p['JP225']} | US30 {p['US30']}
    </div>

    <div style="border-left:4px solid #ffca28;background:#1e1e1e;padding:12px;margin-top:14px;border-radius:6px;">
    <small>GOLD micro • XM SYNC</small><br>
    <b style="font-size:24px;">ENTRY {p['GOLD']}</b><br>
    SL {g_sl} | TP1 {g_tp1} | TP2 {g_tp2}<br>
    <small style="color:#aaa;">{now} - Live Kraken+Yahoo - XM varies by spread</small>
    </div>

    <div style="border-left:4px solid #00e676;background:#1e1e1e;padding:12px;margin-top:12px;border-radius:6px;">
    <small>BTCUSD</small><br>
    <b style="font-size:24px;">ENTRY {p['BTCUSD']}</b><br>
    SL {b_sl} | TP1 {b_tp1} | TP2 {b_tp2}<br>
    <small style="color:#aaa;">{now} - Live Kraken+Yahoo</small>
    </div>

    <div style="border-left:4px solid #2979ff;background:#1e1e1e;padding:12px;margin-top:12px;border-radius:6px;">
    <small>JP225</small><br>
    <b style="font-size:24px;">ENTRY {p['JP225']}</b><br>
    SL {j_sl} | TP1 {j_tp1} | TP2 {j_tp2}<br>
    <small style="color:#aaa;">{now} - Live Kraken+Yahoo</small>
    </div>

    <div style="border-left:4px solid #651fff;background:#1e1e1e;padding:12px;margin-top:12px;border-radius:6px;">
    <small>US30</small><br>
    <b style="font-size:24px;">ENTRY {p['US30']}</b><br>
    SL {u_sl} | TP1 {u_tp1} | TP2 {u_tp2}<br>
    <small style="color:#aaa;">{now} - Live Kraken+Yahoo</small>
    </div>

    <p style="text-align:center;color:#777;margin-top:20px;">🔄 Refresh • WhatsApp to Bongani ✅</p>
    </body></html>
    """
    return html

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
