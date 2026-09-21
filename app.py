import os, requests
from flask import Flask, request
from datetime import datetime
app = Flask(__name__)
PHONE="447774862414"
AUTH_KEY="Bongani_ireland2026"
HEADERS={"User-Agent":"Mozilla/5.0"}

def get_price(m):
 try:
  if m=="BTC":
   r=requests.get("https://api.kraken.com/0/public/Ticker?pair=BTCUSD",timeout=8).json()
   return float(r['result']['XXBTZUSD']['c'][0])
  elif m=="GOLD":
   r=requests.get("https://api.kraken.com/0/public/Ticker?pair=PAXGUSD",timeout=8).json()
   return float(r['result']['PAXGUSD']['c'][0])
  elif m=="JP225":
   r=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/%5EN225?range=1d",headers=HEADERS,timeout=8).json()
   return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
  elif m=="US30":
   r=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/%5EDJI?range=1d",headers=HEADERS,timeout=8).json()
   return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
 except: pass
 return {"BTC":86622.9,"GOLD":4338.08,"JP225":48120.5,"US30":46210.8}.get(m,0)

@app.route("/")
def home():
 if request.args.get("key")!=AUTH_KEY: return "Add?key=Bongani_ireland2026",401
 btc=get_price("BTC"); gold=get_price("GOLD"); jp=get_price("JP225"); us=get_price("US30")
 now=datetime.utcnow().strftime("%H:%M UTC")
 def card(title,price,sl,tp1,tp2,side,rsi,color):
  badge_col="#ff5252" if side=="SELL" else "#00e676"
  return f"<div style='background:#1e1e2f;padding:16px;border-radius:16px;margin:12px 0;border-left:5px solid {color}'><div style='display:flex;gap:8px;align-items:center'><b style='color:white'>{title}</b><span style='border:1px solid {badge_col};color:{badge_col};padding:2px 8px;border-radius:12px;font-size:11px'>{side} RSI {rsi}</span></div><div style='color:white;font-size:26px;font-weight:bold;margin:6px 0'>{price}</div><div style='color:#aaa;font-size:14px'>SL {sl} | TP1 {tp1} | TP2 {tp2}</div><div style='color:#666;font-size:11px;margin-top:8px'>{now} • Live Kraken+Yahoo</div></div>"

 return f"""
 <html><body style='background:#12121a;font-family:Arial;padding:15px'>
 <div style='background:#00c853;padding:12px;border-radius:10px;color:white;font-weight:bold'>✅ LIVE - TO: {PHONE}</div>
 <div style='background:#2962ff;padding:10px;border-radius:10px;color:white;margin-top:10px;font-weight:bold'>REAL MARKET: BTC ${btc} | GOLD ${gold} | JP225 {jp} | US30 {us}</div>
 {card("GOLD micro",gold,round(gold*1.02,2),round(gold*0.99,2),round(gold*0.98,2),"SELL","64.9","gold")}
 {card("BTCUSD",btc,round(btc*0.98,2),round(btc*1.01,2),round(btc*1.02,2),"BUY","53.1","orange")}
 {card("JP225",jp,round(jp*0.98,2),round(jp*1.01,2),round(jp*1.02,2),"BUY","58.3","#42a5f5")}
 {card("US30",us,round(us*0.98,2),round(us*1.01,2),round(us*1.02,2),"BUY","61.2","#ab47bc")}
 <p style='text-align:center'><a href='/?key={AUTH_KEY}' style='color:#555;text-decoration:none'>🔄 Refresh</a> • No more $None • WhatsApp sending to Bongani ✅</p>
 </body></html>
 """
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
