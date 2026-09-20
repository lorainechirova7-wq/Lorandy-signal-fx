from flask import Flask, request
import requests, re, random, os, threading, time
app = Flask(__name__)

TOKEN = os.getenv("WHATSAPP_TOKEN","")
PHONE_ID = os.getenv("WHATSAPP_PHONE_ID","")
TO = os.getenv("TO_NUMBER","447774862414")

WATCH = [
 {"symbol":"BTCUSD","side":"BUY","entry":77800,"sl":77720,"tp":85000},
 {"symbol":"BTCUSD","side":"SELL","entry":85000,"sl":85080,"tp":80000},
 {"symbol":"XAUUSD","side":"BUY","entry":4300,"sl":4295,"tp":4450},
 {"symbol":"XAUUSD","side":"SELL","entry":4450,"sl":4455,"tp":4300},
]

def send_wa(text):
 if not TOKEN or not PHONE_ID:
  print("Missing TOKEN")
  return False
 try:
  url = f"https://graph.facebook.com/v20.0/{PHONE_ID}/messages"
  h = {"Authorization": f"Bearer {TOKEN}", "Content-Type":"application/json"}
  p = {"messaging_product":"whatsapp","to":TO,"type":"text","text":{"body":text}}
  r = requests.post(url, json=p, headers=h, timeout=15)
  print(r.text)
  return r.status_code==200
 except Exception as e:
  print(e)
  return False

@app.route('/')
def home():
 return f"<h1>✅ LIVE - TO: {TO}</h1><a href='/send_test'>TEST WA</a><br><a href='/signal?symbol=BTCUSD&side=BUY&entry=77800&tp=85000'>BTC Test</a>"

@app.route('/send_test')
def send_test():
 ok = send_wa("✅ TEST OK! Bot is LIVE for "+TO)
 return f"Sent={ok} to {TO} - check Render Logs" if ok else "Failed - check TOKEN in Render ENV"

@app.route('/signal')
def signal():
 s=request.args.get('symbol','BTCUSD')
 side=request.args.get('side','BUY')
 entry=request.args.get('entry','77800')
 msg=f"🚨 SIGNAL {s} {side} at {entry} - https://whatsapp-signal-bot.onrender.com/"
 send_wa(msg)
 return f"Signal sent to {TO}"

if __name__ == '__main__':
 app.run(host='0.0.0.0', port=10000)
