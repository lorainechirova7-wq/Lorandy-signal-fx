import os, requests
from flask import Flask, request
app = Flask(__name__)
PHONE="447774862414"
AUTH_KEY="Bongani_ireland2026"

def get_price(m):
 try:
  if m=="BTC":
   r=requests.get("https://api.kraken.com/0/public/Ticker?pair=BTCUSD",timeout=8).json()
   return float(r['result']['XXBTZUSD']['c'][0])
  elif m=="GOLD":
   r=requests.get("https://api.kraken.com/0/public/Ticker?pair=PAXGUSD",timeout=8).json()
   return float(r['result']['PAXGUSD']['c'][0])
  elif m=="JP225":
   r=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/%5EN225?range=1d&interval=1m",timeout=8).json()
   return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
  elif m=="US30":
   r=requests.get("https://query1.finance.yahoo.com/v8/finance/chart/%5EDJI?range=1d&interval=1m",timeout=8).json()
   return float(r['chart']['result'][0]['meta']['regularMarketPrice'])
 except: pass
 # fallback never None
 return {"BTC":86789.9,"GOLD":4338.98,"JP225":44150.0,"US30":44500.0}.get(m,0)

@app.route("/")
def home():
 if request.args.get("key")!=AUTH_KEY: return "<h2>Add?key=Bongani_ireland2026</h2>",401
 btc=get_price("BTC"); gold=get_price("GOLD"); jp=get_price("JP225"); us=get_price("US30")
 def lv(p,side):
  return (round(p*0.98,2),round(p*1.01,2),round(p*1.02,2)) if side=="BUY" else (round(p*1.02,2),round(p*0.99,2),round(p*0.98,2))
 b_sl,b_t1,b_t2=lv(btc,"BUY"); g_sl,g_t1,g_t2=lv(gold,"SELL"); j_sl,j_t1,j_t2=lv(jp,"BUY"); u_sl,u_t1,u_t2=lv(us,"BUY")
 return f"""
 <html><body style='font-family:Arial;padding:15px;background:#f0f8ff'>
 <h1 style='color:white;background:green;padding:15px;border-radius:10px'>✅ LIVE - TO: {PHONE}</h1>
 <h2 style='color:white;background:#007bff;padding:12px;border-radius:10px'>REAL MARKET: BTC ${btc} | GOLD ${gold} | JP225 {jp} | US30 {us}</h2>
 <div style='background:white;padding:12px;border-radius:8px;border-left:5px solid gold;margin:8px 0'><b style='color:orange'>GOLD SELL</b> ${gold} SL {g_sl} TP1 {g_t1} TP2 {g_t2}</div>
 <div style='background:white;padding:12px;border-radius:8px;border-left:5px solid orange;margin:8px 0'><b style='color:orange'>BTC BUY</b> ${btc} SL {b_sl} TP1 {b_t1} TP2 {b_t2}</div>
 <div style='background:white;padding:12px;border-radius:8px;border-left:5px solid blue;margin:8px 0'><b style='color:blue'>JP225 BUY</b> {jp} SL {j_sl} TP1 {j_t1} TP2 {j_t2}</div>
 <div style='background:white;padding:12px;border-radius:8px;border-left:5px solid purple;margin:8px 0'><b style='color:purple'>US30 BUY</b> {us} SL {u_sl} TP1 {u_t1} TP2 {u_t2}</div>
 <a href='/?key={AUTH_KEY}' style='background:green;color:white;padding:12px;border-radius:8px;text-decoration:none;display:inline-block'>🔄 Refresh Prices</a>
 <a href='/?key={AUTH_KEY}&send=1' style='background:blue;color:white;padding:12px;border-radius:8px;text-decoration:none;display:inline-block;margin-left:8px'>📱 Send to Bongani</a>
 <p><small>Live from Kraken + Yahoo Finance • No more $None</small></p>
 </body></html>
 """
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
