import os
from flask import Flask, jsonify, request

app = Flask(__name__)

PHONE_NUMBER = os.getenv('PHONE_NUMBER', '+26774959070')
MAX_RISK_PIPS = int(os.getenv('MAX_RISK', '30'))

@app.route('/')
def home():
    return f"✅ Lorandy-signal-fx LIVE! Sending to {PHONE_NUMBER} | Max Risk {MAX_RISK_PIPS} pips | USD/BTC/US30 Allowed"

@app.route('/signal', methods=['POST','GET'])
def signal():
    data = request.json or {}
    entry = float(data.get('entry', 1.2000))
    sl = float(data.get('sl', 1.2020))
    symbol = data.get('symbol', 'USD').upper()
    
    # Auto pip value
    if 'JPY' in symbol:
        pip_value = 0.01
    elif 'XAU' in symbol or 'GOLD' in symbol:
        pip_value = 0.1
    elif 'BTC' in symbol or 'US30' in symbol or 'NAS' in symbol or 'USTEC' in symbol:
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
    
    return jsonify({
        "status": "OK",
        "symbol": symbol,
        "risk_pips": round(risk_pips, 1),
        "send_to": PHONE_NUMBER,
        "whatsapp_message": f"✅ {symbol} BUY Entry {entry} SL {sl} - Risk {risk_pips:.1f} pips"
    })

if __name__ == '__main__':
    app.run()
