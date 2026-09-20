import os
import requests
from flask import Flask, jsonify, request

app = Flask(__name__)

PHONE_NUMBER = os.getenv('PHONE_NUMBER', '+26774959070')
MAX_RISK_PIPS = int(os.getenv('MAX_RISK_PIPS', '30'))
CALLMEBOT_APIKEY = os.getenv('CALLMEBOT_APIKEY', '')

@app.route('/')
def home():
    return f"✅ Lorandy-signal-fx LIVE! Sending to {PHONE_NUMBER} | Max Risk {MAX_RISK_PIPS} pips | USD/BTC/US30 Allowed | CallMeBot: {'ON' if CALLMEBOT_APIKEY else 'NO KEY YET'}"

@app.route('/signal', methods=['POST'])
def signal():
    data = request.json or {}
    entry = float(data.get('entry', 1.2000))
    sl = float(data.get('sl', 1.2020))
    symbol = data.get('symbol', 'USD').upper()

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
        return jsonify({
            "status": "SKIPPED",
            "reason": f"Over {MAX_RISK_PIPS} pips",
            "symbol": symbol,
            "risk_pips": round(risk_pips, 1),
            "send_to": PHONE_NUMBER
        })

    msg = f"✅ {symbol} BUY\nEntry: {entry}\nSL: {sl}\nRisk: {round(risk_pips,1)} pips\nTo: {PHONE_NUMBER}"
    
    # SEND WHATSAPP VIA CALLMEBOT
    if CALLMEBOT_APIKEY:
        try:
            url = f"https://api.callmebot.com/whatsapp.php?phone={PHONE_NUMBER}&text={msg}&apikey={CALLMEBOT_APIKEY}"
            requests.get(url, timeout=10)
        except Exception as e:
            print(e)

    return jsonify({
        "status": "OK",
        "symbol": symbol,
        "risk_pips": round(risk_pips, 1),
        "send_to": PHONE_NUMBER,
        "whatsapp_message": msg,
        "whatsapp_sent": bool(CALLMEBOT_APIKEY)
    })

if __name__ == '__main__':
    app.run()
