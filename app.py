from flask import Flask, request, render_template_string
import requests, yfinance as yf, random
from datetime import datetime

app = Flask(__name__)

# CONFIG
SITE_KEY = "1511193"
WHATSAPP_PHONE = "447774862414"
WHATSAPP_APIKEY = "1511193"
GOLD_ALERT = 4340.0

# Store last signal to stop scalping
last_signals = {}

# 200 PIPS DEFINITION (XM)
PIPS_200 = {
    "GOLD": 20.0, # 200 pips = $20.0 (1 pip = $0.1)
    "BTCUSD": 200.0, # 200 pips = $200
    "JP225": 200.0, # 200 points
    "US30": 200.0 # 200 points
}

# SL = 1R
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
    # GOLD live
    try:
        r = requests.get("https://api.gold-api.com/price/XAU", timeout=5).json()
        prices["GOLD"] = float(r['price'])
    except:
        prices["GOLD"] = 4317.4

    # Yahoo for others - XM exact in 2026
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
    """200 PIPS ANALYSIS"""
    try:
        ticker = yf.Ticker(yahoo_symbol)
        hist = ticker.history(period="5d", interval="15m")
        if len(hist) < 20:
            hist = ticker.history(period="2d", interval="5m")

        # Price 12 hours ago
        old_price = hist['Close'].iloc[-48] if len(hist) > 48 else hist['Close'].iloc[0]
        move = current_price - old_price
        move_pips = abs(move) / (0.1 if symbol=="GOLD" else 1) if symbol=="GOLD" else abs(move)

        # 200 pips threshold
        threshold = PIPS_200[symbol]

        if abs(move) >= threshold:
            if move > 0:
                side = "BUY"
                reason = f"+{move:.1f} ({move_pips:.0f} pips) in 12H > 200 pips UPTREND"
            else:
                side = "SELL"
                reason = f"{move:.1f} ({move_pips:.0f} pips) in 12H > 200 pips DOWNTREND"
            last_signals[symbol] = side
            return side, reason, True

        # If less than 200 pips, KEEP last signal to avoid scalping
        if symbol in last_signals:
            side = last_signals[symbol]
            reason = f"Only {move:.1f} ({move_pips:.0f} pips) < 200 pips - KEEP {side} (no scalping)"
            return side, reason, False
        else:
            # First time, decide by move direction
            side = "BUY" if move >=0 else "SELL"
            last_signals[symbol] = side
            reason = f"First signal {move:.1f} ({move_pips:.0f} pips) -> {side}"
            return side, reason, False

    except Exception as e:
        side = last_signals.get(symbol, random.choice(["BUY","SELL"]))
        return side, f"Analysis error, keep {side}", False

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

    return side, round(sl,2), round(tp1,2), round
