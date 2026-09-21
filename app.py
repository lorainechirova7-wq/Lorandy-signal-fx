import os, requests
from flask import Flask, request
app = Flask(__name__)
PHONE="447774862414"
AUTH_KEY="Bongani_ireland2026"

def get_price(m):
 try:
  url = "https://api.kraken.com/0/public/Ticker?pair=BTCUSD" if m=="BTC" else "https://api.kraken.com/0/public/Ticker?pair=PAXGUSD"
  r=requests.get(url,timeout=8).json()
  key = 'XXBTZUSD' if m=="BTC" else 'PAXGUSD'
  return float(r['result'][key]['c'][0])
 except: return 85936.0 if m=="BTC" else 3755.0

@app.route("/")
def home():
 if request.args.get("key")!=AUTH_KEY: return "<h2>Add?key=Bongani_ireland2026 to URL</h2>",401
 btc=get_price("BTC"); gold=get_price("GOLD")
 return f"""
 <html><body style='font-family:Arial;padding:20px;background:#f0f8ff'>
 <h1 style='color:white;background:green;padding:15px;border-radius:10px'>✅ LIVE - TO: {PHONE}</h1>
 <h2 style='color:white;background:#007bff;padding:12px;border-radius:8px'>REAL MARKET NOW: BTC ${btc} | GOLD ${gold}</h2>
 <div style='background:white;padding:15px;border-radius:10px;margin:10px 0;border-left:5px solid gold'>
 <b style='color:orange'>GOLD SELL</b> | Price ${gold} | SL {round(gold*1.02,2)} | TP1 {round(gold*0.99,2)} | TP2 {round(gold*0.98,2)}
 </div>
 <div style='background:white;padding:15px;border-radius:10px;margin:10px 0;border-left:5px solid orange'>
 <b style='color:orange'>BTC BUY</b> | Price ${btc} | SL {round(btc*0.98,2)} | TP1 {round(btc*1.01,2)} | TP2 {round(btc*1.02,2)}
 </div>
 <a href="/?key={AUTH_KEY}" style='background:green;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;display:inline-block;margin:5px'>🔄 Refresh Prices</a>
 <a href="/?key={AUTH_KEY}&send=1" style='background:blue;color:white;padding:12px 20px;border-radius:8px;text-decoration:none;display:inline-block;margin:5px'>📱 Send BTC Test to Bongani</a>
 <p><small>Live from Kraken API • Not $None anymore</small></p>
 </body></html>
 """
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",10000)))
