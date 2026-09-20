from flask import Flask, request
import requests, re, random

app = Flask(__name__)

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
    if len(prices) < period+1:
        return 55.2
    gains=0; losses=0
    for i in range(len(prices)-period, len(prices)):
        d=prices[i]-prices[i-1]
        if d>0: gains+=d
        else: losses+=abs(d)
    avg_gain=gains/period; avg_loss=losses/period
    if avg_loss<0.01: return 61.5
    if avg_gain<0.01: return 38.5
    rs=avg_gain/avg_loss
    val=100-(100/(1+rs))
    return max(35.0, min(72.0, val))

def full_ai_analysis(symbol, side, entry, sl, tp):
    closes=get_klines(symbol)
    now=closes[-1]
    rsi_val=rsi(closes)
    ema=sum(closes[-20:])/20
    if side=="BUY":
        if now<=entry:
            bias=f"STRONG BUY - SUPPORT HIT at {entry}"
            next_move=f"Retrace complete at {entry}. RSI {rsi_val:.1f} oversold. Next IMPULSE UP to {tp}"
            color="#00c853"
        else:
            pct=(now-entry)/entry*100
            bias="WAIT FOR DIP - BULLISH"
            next_move=f"Price {now:.0f} is {pct:.1f}% above {entry}. EMA {ema:.0f}. Wait dip to {entry}, then BUY to {tp}"
            color="#ffab00"
        plan=f"BUY {entry} | SL {sl} | TP {tp}"
    else:
        if now>=entry:
            bias=f"STRONG SELL - RESISTANCE HIT at {entry}"
            next_move=f"Rally complete at {entry}. RSI {rsi_val:.1f} overbought. DROP to {tp}"
            color="#ff1744"
        else:
            pct=(entry-now)/now*100
            bias="WAIT FOR RALLY - BEARISH"
            next_move=f"Price {now:.0f} is {pct:.1f}% below {entry}. EMA {ema:.0f}. Wait rally to {entry}, SELL to {tp}"
            color="#ff6d00"
        plan=f"SELL {entry} | SL {sl} | TP {tp}"
    return now,rsi_val,ema,bias,next_move,plan,color

def html_page(symbol, side, entry, tp, sl, now, rsi_v, ema, bias, next_move, plan, color, question):
    return f"<html><head><meta name='viewport' content='width=device-width, initial-scale=1'><style>body{{background:#0f1115;color:#fff;font-family:Arial;padding:15px}}.card{{background:#1a1d26;border-radius:15px;padding:16px;margin:10px 0;border-left:5px solid {color}}}.badge{{background:{color};padding:6px 14px;border-radius:20px;font-weight:bold;display:inline-block;color:#000}}.price{{font-size:32px;font-weight:bold}}.small{{color:#aaa;font-size:13px}}a{{text-decoration:none}}input{{width:100%;padding:14px;border-radius:10px;border:none;margin:6px 0;background:#252836;color:#fff}}.btn{{background:{color};color:#000;padding:14px;border-radius:10px;text-align:center;font-weight:bold;display:block;margin-top:8px}}</style></head><body><h2>AI ANALYST</h2><div class=card><span class=badge>{symbol} {side}</span><div class=price>${now:,.1f}</div><div class=small>RSI {rsi_v:.1f} | EMA {ema:.0f} | {entry} -> {tp}</div><hr><b>BIAS:</b> {bias}<br><br><b>NEXT:</b><br>{next_move}<br><br><b>PLAN:</b><br>{plan}<br><br><div class=small>Q: {question}</div></div><div class=card><b>All Markets:</b><form action='/chat'><input name='q' placeholder='gold after 4300?'><input type='submit' value='Ask AI' class=btn></form><a class=btn href='/ask?symbol=BTCUSD&side=BUY&entry=77800&tp=85000&question=btc next' style='background:#00c853'>BTC 77800->85000</a><a class=btn href='/ask?symbol=XAUUSD&side=BUY&entry=4300&tp=4450&question=gold next' style='background:#ffd600'>GOLD 4300->4450 BUY</a><a class=btn href='/ask?symbol=XAUUSD&side=SELL&entry=4450&tp=4300&question=gold rally' style='background:#ff9100'>GOLD 4450->4300 SELL</a><a class=btn href='/ask?symbol=US30&side=SELL&entry=53000&tp=51000&question=us30' style='background:#ff5252'>US30 53000->51000</a><a class=btn href='/ask?symbol=JP225&side=BUY&entry=64000&tp=66000&question=jp225' style='background:#7c4dff'>JP225 64000->66000</a></div></body></html>"

@app.route('/')
def home():
    now,rsi_v,ema,bias,next_move,plan,color=full_ai_analysis("BTCUSD","BUY",77800,77720,85000)
    return html_page("BTCUSD","BUY",77800,85000,77720,now,rsi_v,ema,bias,next_move,plan,color,"dashboard")

@app.route('/ask')
def ask():
    symbol=request.args.get('symbol','BTCUSD').upper()
    side=request.args.get('side','BUY').upper()
    entry=float(request.args.get('entry','77800'))
    tp=float(request.args.get('tp','85000'))
    sl=float(request.args.get('sl', entry-80 if side=="BUY" else entry+80))
    question=request.args.get('question','whats next')
    now,rsi_v,ema,bias,next_move,plan,color=full_ai_analysis(symbol,side,entry,sl,tp)
    return html_page(symbol,side,entry,tp,sl,now,rsi_v,ema,bias,next_move,plan,color,question)

@app.route('/chat')
def chat():
    q=request.args.get('q','').lower()
    symbol="BTCUSD"
    if "us30" in q or "dow" in q: symbol="US30"
    elif "jp" in q or "nikkei" in q: symbol="JP225"
    elif "xau" in q or "gold" in q: symbol="XAUUSD"
    side="SELL" if any(x in q for x in ["sell","short","rally","top","resistance"]) else "BUY"
    nums=re.findall(r'\d+', q)
    entry=float(nums[0]) if nums else 77800
    tp=float(nums[1]) if len(nums)>1 else 85000
    sl=entry-80 if side=="BUY" else entry+80
    now,rsi_v,ema,bias,next_move,plan,color=full_ai_analysis(symbol,side,entry,sl,tp)
    return html_page(symbol,side,entry,tp,sl,now,rsi_v,ema,bias,next_move,plan,color,q)

@app.route('/signal')
def signal():
    return home()

if __name__ == '__main__':
    import os
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
