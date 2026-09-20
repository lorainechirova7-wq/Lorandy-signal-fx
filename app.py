import os
import requests
import urllib.parse
from flask import Flask, jsonify, request

app = Flask(__name__)

PHONE_NUMBER = os.getenv('PHONE_NUMBER', os.getenv('CALLMEBOT_PHONE', '447774862414'))
MAX_RISK_PIPS = int(os.getenv('MAX_RISK_PIPS', '30'))
CALLMEBOT_APIKEY = os.getenv('CALLMEBOT_APIKEY', '1511193')

@app.route('/')
def home():
    return f"✅ LIVE! To {PHONE_NUMBER} | Max {MAX_RISK_PIPS} pips | CallMeBot: {'ON' if CALLMEBOT_APIKEY else 'OFF'}"

@app.route('/signal', methods=['GET','POST'])
def signal():
    if request.method == 'GET':
        data = request.args
    else:
        data = request.json or {}
    entry = float(data.get('entry', 1.2000))
    sl = float(data.get('sl', 1.1980))
    symbol = data.get('symbol', 'EURUSD').upper()

    if 'JPY' in symbol:
        pip_value = 0.01
    elif 'XAU' in symbol or 'GOLD' in symbol:
        pip_value = 0.1
    elif 'BTC' in symbol or 'US30' in symbol:
        pip_value = 1.0
    else:
        pip_value = 0.0001

    risk_pips = abs(entry - sl) / pip_value

    if risk_pips > MAX_RISK_PIPS:
        return jsonify({"status": "SKIPPED", "reason": f"Over {MAX_RISK_PIPS} pips"})

    msg = f"✅ {symbol} BUY\nEntry: {entry}\nSL: {sl}\nRisk: {round(risk_pips,1)} pips"
    encoded_msg = urllib.parse.quote(msg)

    if CALLMEBOT_APIKEY:
        try:
            url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE_NUMBER}&text={encoded_msg}&apikey={CALLMEBOT_APIKEY}"
            requests.get(url, timeout=15)
        except Exception as e:
            print(e)

    return jsonify({"status": "OK - WhatsApp sent!", "symbol": symbol, "risk_pips": round(risk_pips,1), "send_to": PHONE_NUMBER})

if __name__ == '__main__':
    app.run()
