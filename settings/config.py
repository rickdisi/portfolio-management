import json, os

# 1) Figure out where config.json lives:
BASE = os.path.dirname(__file__)
path = os.path.join(BASE, "config.json")

# 2) Load it exactly once:
with open(path) as f:
    _data = json.load(f)

# 3) Expose values as module globals:
globals().update(_data)

MAX_POSITION_PER_TICKER = max(
    TARGET_WEIGHTS["FICC"]   / len(FICC_TICKERS), # type: ignore
    TARGET_WEIGHTS["EQUITY"] / len(EQUITY_TICKERS), # type: ignore
    TARGET_WEIGHTS["ETF"]    / len(ETF_TICKERS), # type: ignore
)