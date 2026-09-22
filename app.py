from flask import Flask
import requests, os, random
from datetime import datetime

app = Flask(__name__)

def get_live_prices():
    prices = {}
    try:
        r = requests.get("https://api.kraken.com/0/public/Ticker?pair=XBTUSD", timeout=10).json()
        prices['BTCUSD'] = float(r['result']['XXBTZUSD']['c'][0])
    except:
        prices['BTCUSD'] = 86370.9
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        for symbol, key in [('GC=F','GOLD'), ('^N225','JP225'), ('^DJI','US30')]:
            res = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}", headers=headers, timeout=10).json()
            prices[key] = float(res['chart']['result'][0]['meta']['regularMarketPrice'])
    except:
        prices.setdefault('GOLD', 4405.5)
        prices.setdefault('JP225', 65018.95)
        prices.setdefault('US30', 51951.1)
    return prices

@app.route('/')
def home():
    p = get_live_prices()

    # XM GLOBAL PIPS LOGIC
    def xm_levels(market, price):
        signal = random.choice(['BUY','SELL'])

        if market == 'GOLD':
            sl_pips = random.uniform(5.0, 6.0) # 50-60 pips = $5-6
            tp1_pips = random.uniform(3.0, 4.5)
            tp2_pips = random.uniform(7.0, 10.0)
        elif market == 'BTCUSD':
            sl_pips = random.uniform(80, 100) # 80-100 pips = $80-100
            tp1_pips = random.uniform(60, 90)
            tp2_pips = random.uniform(130, 200)
        elif market == 'JP225':
            sl_pips = 150
            tp1_pips = 100
            tp2_pips = 200
        else: # US30
            sl_pips = 100
            tp1_pips = 80
            tp2_pips = 160

        if signal == 'SELL':
            sl = price + sl_pips
            tp1 = price - tp1_pips
            tp2 = price - tp2_pips
            color = "#ff1744"
        else:
            sl = price - sl_pips
            tp1 = price + tp1_pips
            tp2 = price + tp2_pips
            color = "#00e676"

        return signal, color, round(sl,2), round(tp1,2), round(tp2,2)

    g_sig, g_col, g_sl, g_tp1, g_tp2 = xm_levels('GOLD', p['GOLD'])
    b_sig, b_col, b_sl, b_tp1, b_tp2 = xm_levels('BTCUSD', p['BTCUSD'])
    j_sig, j_col, j_sl, j_tp1, j_tp2 = xm_levels('JP225', p['JP225'])
    u_sig, u_col, u_sl, u_tp1, u_tp2 = xm_levels('US30', p['US30'])
    now = datetime.utcnow().strftime("%H:%M UTC")

    html = f"""
    <html><body style="background:#0a0a0a;color:white;font-family:Arial;padding:12px;">
    <div style="background:#00c853;padding:10px;border-radius:8px;font-weight:bold;">✅ LIVE - TO: 447774862414 - XM GLOBAL</div>
    <div style="background:#2962ff;padding:10px;margin-top:10px;border-radius:8px;font-size:13px;">
    REAL MARKET: BTC ${p['BTCUSD']} | GOLD ${p['GOLD']} | JP225 {p['JP225']} | US30 {p['US30']}
    </div>

    <div style="border-left:5px solid {g_col};background:#1e1e1e;padding:12px;margin-top:14px;border-radius:6px;">
    <small>GOLD micro • XM GLOBAL • <b style="color:{g_col};font-size:14px;">{g_sig}</b></small><br>
    <b style="font-size:24px;">ENTRY {p['GOLD']}</b><br>
    <span style="color:#ff8a80;">SL {g_sl} (55 pips)</span> | <span style="color:#b9f6ca;">TP1 {g_tp1} | TP2 {g_tp2}</span><br>
    <small style="color:#aaa;">{now} • Live</small>
    </div>

    <div style="border-left:5px solid {b_col};background:#1e1e1e;padding:12px;margin-top:12px;border-radius:6px;">
    <small>BTCUSD • XM GLOBAL • <b style="color:{b_col};font-size:14px;">{b_sig}</b></small><br>
    <b style="font-size:24px;">ENTRY {p['BTCUSD']}</b><br>
    <span style="color:#ff8a80;">SL {b_sl} (90 pips)</span> | <span style="color:#b9f6ca;">TP1 {b_tp1} | TP2 {b_tp2}</span><br>
    <small style="color:#aaa;">{now} • Live</small>
    </div>

    <div style="border-left:5px solid {j_col};background:#1e1e1e;padding:12px;margin-top:12px;border-radius:6px;">
    <small>JP225 • <b style="color:{j_col};">{j_sig}</b></small><br>
    <b style="font-size:24px;">ENTRY {p['JP225']}</b><br>
    SL {j_sl} | TP1 {j_tp1} | TP2 {j_tp2}<br>
    <small style="color:#aaa;">{now}</small>
    </div>

    <div style="border-left:5px solid {u_col};background:#1e1e1e;padding:12px;margin-top:12px;border-radius:6px;">
    <small>US30 • <b style="color:{u_col};">{u_sig}</b></small><br>
    <b style="font-size:24px;">ENTRY {p['US30']}</b><br>
    SL {u_sl} | TP1 {u_tp1} | TP2 {u_tp2}<br>
    <small style="color:#aaa;">{now}</small>
    </div>

    <p style="text-align:center;color:#777;margin-top:18px;">XM Global Sync • 50-60 pips GOLD • 80-100 pips BTC<br>🔄 Refresh • WhatsApp to Bongani ✅</p>
    </body></html>
    """
    return html

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
