from flask import Flask, jsonify, request
app = Flask(__name__)

# CUSTOMER RULE: Don't risk over 30 pips
MAX_RISK_PIPS = 30

@app.route('/')
def home():
    return f"Lorandy-signal-fx LIVE - Max risk {MAX_RISK_PIPS} pips (BTC & US30 included)"

@app.route('/signal', methods=['POST','GET'])
def signal():
    data = request.json or {}
    entry = float(data.get('entry', 1.2000))
    sl = float(data.get('sl', 1.2020))
    symbol = data.get('symbol', 'USD').upper()
    
    # Pip value for different symbols
    if 'JPY' in symbol:
        pip_value = 0.01
    elif 'XAU' in symbol or 'GOLD' in symbol:
        pip_value = 0.1
    elif 'BTC' in symbol:
        pip_value = 1.0
    elif 'US30' in symbol or 'USTEC' in symbol or 'NAS' in symbol:
        pip_value = 1.0
    else:
        pip_value = 0.0001
        
    risk_pips = abs(entry - sl) / pip_value
    
    if risk_pips > MAX_RISK_PIPS:
        return jsonify({
            "status": "SKIPPED",
            "reason": f"Risk {risk_pips:.1f} pips > {MAX_RISK_PIPS} pips limit",
            "symbol": symbol,
            "risk_pips": round(risk_pips, 1)
        })
    
    return jsonify({
        "status": "OK - Signal Valid",
        "symbol": symbol,
        "risk_pips": round(risk_pips, 1),
        "max_allowed": MAX_RISK_PIPS
    })

if __name__ == '__main__':
    app.run()
