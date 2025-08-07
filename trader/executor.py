import logging, os, numpy as np
from datetime import datetime
from pathlib import Path
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce

from dotenv import load_dotenv
load_dotenv() 

log_dir = Path(__file__).parent / "data"
LOG_PATH = os.getenv("tradelog_path", os.path.join(log_dir, "trade_log.csv"))

if not os.path.exists(LOG_PATH):
    # write header if file doesn’t exist
    with open(LOG_PATH, "w") as f:
        f.write("timestamp,symbol,side,qty,price,nav\n")

logger = logging.getLogger("trade_executor")
logger.setLevel(logging.INFO)

# (optionally add a stream handler for console)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("%(asctime)s — %(message)s"))
logger.addHandler(ch)

client = TradingClient(os.getenv("alpaca_key"), os.getenv("alpaca_secret"), paper=True)

def submit_orders(target_weights, latest_prices, nav):
    positions = client.get_all_positions()
    cash_left  = float(client.get_account().cash) # type: ignore
    current_qty = {p.symbol: float(p.qty) for p in positions} # type: ignore

    # Emergency sell if cash is negative
    if cash_left < 0:
        # sort symbols by largest position value first
        sorted_syms = sorted(
            current_qty.keys(),
            key=lambda s: current_qty[s] * latest_prices.get(s, 0),
            reverse=True
        )
        for symbol in sorted_syms:
            if cash_left >= 0:
                break
            price    = latest_prices.get(symbol, np.nan)
            qty_hold = current_qty.get(symbol, 0)
            if qty_hold <= 0 or np.isnan(price):
                continue

            # how many shares to sell to cover the negative cash
            needed_shares = int(np.ceil(abs(cash_left) / price))
            sell_qty = min(qty_hold, needed_shares)

            # submit the sell
            req = MarketOrderRequest(
                symbol=symbol,
                qty=sell_qty,
                side=OrderSide.SELL,
                time_in_force=TimeInForce.DAY
            )
            client.submit_order(req)

            # update in-memory cash and qty
            cash_left   += sell_qty * price
            current_qty[symbol] -= sell_qty

    for symbol, w in target_weights.items():

        price = latest_prices.get(symbol, np.nan)
        if np.isnan(price):
            # skip symbols with no price
            print(f"Skipping {symbol}: no latest price")
            continue
    
        tgt_dollar = w * nav
        curr_dollar = current_qty.get(symbol, 0) * latest_prices[symbol]
        delta_dollar = tgt_dollar - curr_dollar

        if abs(delta_dollar) < 1: # ignore dust
            continue
        side = OrderSide.BUY if delta_dollar > 0 else OrderSide.SELL
        
        raw_qty = abs(int(delta_dollar // latest_prices[symbol]))

        if side == OrderSide.SELL:
            max_sellable = current_qty.get(symbol, 0)
            qty = min(raw_qty, max_sellable)
            cash_left += qty * price
        else:
            if cash_left <= 0:
                continue

            max_affordable = int(cash_left // price)
            if max_affordable <= 0:
                continue

            qty = min(raw_qty, max_affordable)
            cash_left -= qty * price

        if qty == 0:
            continue

        ts = datetime.now().isoformat()
        log_line = f"{ts},{symbol},{side.name},{qty},{price:.2f},{nav:.2f}\n"
        with open(LOG_PATH, "a") as f:
            f.write(log_line)
        logger.info(f"Logging trade → {log_line.strip()}")

        req = MarketOrderRequest(symbol=symbol, qty=qty,
                                  side=side,
                                  time_in_force=TimeInForce.DAY)
        client.submit_order(req)
