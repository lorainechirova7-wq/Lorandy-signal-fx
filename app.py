#... keep everything same until get_trend_200pips...

# CHANGE this function ONLY to this fixed one:

def get_trend_200pips(symbol, current_price):
    # First time only - set entry once and keep it
    if symbol not in last_signals:
        # If GOLD below 4340 -> start as SELL, else BUY
        if symbol == "GOLD" and current_price <= GOLD_ALERT:
            init_side = "SELL"
        else:
            init_side = "BUY"
        last_signals[symbol] = {"side": init_side, "entry": current_price, "time": datetime.now()}
        return init_side, f"START {init_side} at {current_price} - waiting for 200 pips move", False

    entry = last_signals[symbol]["entry"]
    old_side = last_signals[symbol]["side"]
    move = current_price - entry
    move_pips = abs(move) / 0.1 if symbol == "GOLD" else abs(move)
    threshold_price = 20.0 if symbol == "GOLD" else 200.0

    if abs(move) >= threshold_price:
        new_side = "BUY" if move > 0 else "SELL"
        last_signals[symbol] = {"side": new_side, "entry": current_price, "time": datetime.now()}
        return new_side, f"{move:+.1f} ({move_pips:.0f} pips) >200pips! {old_side} -> {new_side} TREND CONFIRMED", True
    else:
        return old_side, f"{move:+.1f} ({move_pips:.0f} pips) from entry {entry} | Holding {old_side} until {threshold_price} move - No scalping flip", False
