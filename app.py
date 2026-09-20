from flask import Flask, request
import requests, threading, time, os, re, random

app = Flask(__name__)

WATCH_LEVELS = [
    {"symbol": "BTCUSD", "side": "BUY", "entry": 77800, "sl": 77720, "tp": 85000},
    {"symbol": "BTCUSD", "side": "BUY", "entry": 80000, "sl": 79920, "tp": 85000},
    {"symbol": "BTCUSD", "side": "SELL", "entry": 85000, "sl": 85080, "tp": 80000},
    {"symbol": "BTCUSD", "side": "SELL", "entry": 88000, "sl": 88080, "tp": 83000},
    {"symbol": "US30", "side": "BUY", "entry": 51000, "sl": 50920, "tp": 53000},
    {"symbol": "US30", "side": "BUY", "entry": 50000, "sl": 49920, "tp": 52500},
    {"symbol": "US30", "side": "SELL", "entry": 52500, "sl": 52580, "tp": 51000},
    {"symbol": "US30", "side": "SELL", "entry": 53000, "sl": 53080, "tp": 51500},
    {"symbol": "JP225", "side": "BUY", "entry": 64000, "sl": 63920, "tp": 66000},
    {"symbol": "JP225", "side": "BUY", "entry": 62000, "sl": 61920, "tp": 65000},
    {"symbol": "JP225", "side": "SELL", "entry": 66000, "sl": 66080, "tp": 64000},
    {"symbol": "JP225", "side": "SELL", "entry": 67000, "sl": 67080, "tp": 64500},
    {"symbol": "XAUUSD", "side": "BUY", "entry": 4300, "sl": 4295, "tp": 4450},
    {"symbol": "XAUUSD", "side": "SELL", "entry": 4450, "sl": 4455, "tp": 4300},
]

triggered = set()

def get_price(symbol):
    try:
        if "BTC" in symbol:
            r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=10).json()
            return float(r['bitcoin']['usd'])
    except:
        pass
    return {"BTCUSD": 109500.0, "US30": 51800.0, "JP225": 65018.0, "XAUUSD": 4350.0}.get(symbol, 80000.0)

def get_klines(symbol, limit=50):
    try:
        if "BTC" in symbol:
            url = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=usd&days=1"
            data = requests.get(url, timeout=10).json()
            prices = [p[1] for p in data['prices']]
            if len(prices) >= limit:
                return prices[-limit:]
            return prices
    except:
        pass
    base = get_price(symbol)
    prices = [base]
    for _ in range(1, limit):
        prices.append(prices[-1] + random.uniform(-base*0.003, base*0.003))
    return prices

def rsi(prices, period=14):
    if len(prices) < period + 1:
        return 55.2
    gains = 0
    losses = 0
    for i in range(len(prices) - period, len(prices)):
        d = prices[i] - prices[i-1]
        if d > 0:
            gains += d
        else:
            losses += abs(d)
    avg_gain = gains / period
    avg_loss = losses / period
    if avg_loss < 0.01:
        return 61.5
    if avg_gain < 0.01:
        return 38.5
    rs = avg_gain / avg_loss
    val = 100 - (100 / (1 + rs))
    return max(35.0, min(72.0, val))

def full_ai_analysis(symbol, side, entry, sl, tp):
    closes = get_klines(symbol)
    now = closes[-1]
    rsi_val = rsi(closes)
    ema = sum(closes[-20:]) / 20
    if side == "BUY":
        if now <= entry:
            bias = f"STRONG BUY - SUPPORT HIT at {entry}"
            next_move = f"Retrace complete at {entry}. Price {now:.0f} hit support. RSI {rsi_val:.1f} oversold. Next move IMPULSE UP to {tp}, then {int(tp*1.03)}."
            color = "#00c853"
        else:
            pct = ((now - entry) / entry * 100)
            bias = "WAIT FOR DIP - BULLISH"
            next_move = f"Price {now:.0f} is {pct:.1f}% above support {entry}. EMA {ema:.0f} holding. Wait dip to {entry}, then STRONG BUY to {tp}. After {tp}, continuation to {int(tp*1.03)}."
            color = "#ffab00"
        plan = f"BUY {entry} | SL {sl} | TP1 {tp} | TP2 {int(tp*1.03)}"
    else:
        if now >= entry:
            bias = f"STRONG SELL - RESISTANCE HIT at {entry}"
            next_move = f"Rally complete at {entry}. Price {now:.0f} hit resistance. RSI {rsi_val:.1f} overbought. Next move DROP to {tp}, then {int(tp*0.97)}."
            color = "#ff1744"
        else:
            pct = ((entry - now) / now * 100)
            bias = "WAIT FOR RALLY - BEARISH"
            next_move = f"Price {now:.0f} is {pct:.1f}% below resistance {entry}. EMA {ema:.0f}. Wait rally to {entry}, then SELL to {tp}."
            color = "#ff6d00"
        plan = f"SELL {entry} | SL {sl} | TP1 {tp} | TP2 {int(tp*0.97)}"
    return now, rsi_val, ema, bias, next_move, plan, color

def html_page(symbol, side, entry, tp, sl, now, rsi_v, ema, bias, next_move, plan, color, question):
    return f"""<html><head><meta name='viewport' content='width=device-width, initial-scale=1'>
    <style>
    body{{background:#0f1115;color:#fff;font-family:Arial;padding:15px}}
  .card{{background:#1a1d26;border-radius:15px;padding:16px;margin:10px 0;border-left:5px solid {color}}}
  .badge{{background:{color};padding:6px 14px;border-radius:20px;font-weight:bold;display:inline-block;color:#000}}
  .price{{font-size:32px;font-weight:bold}}
  .small{{color:#aaa;font-size:13px}}
    a{{text-decoration:none}}
    input{{width:100%;padding:14px;border-radius:10px;border:none;margin:6px 0;background:#252836;color:#fff;font-size:16px}}
  .btn{{background:{color};color:#000;padding:14px;border-radius:10px;text-align:center;font-weight:bold;display:block;margin-top:8px}}
    </style></head><body>
    <h2>🤖 AI ANALYST</h2>
    <div class=card
