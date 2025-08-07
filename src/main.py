import os
import numpy as np
import pandas as pd
import datetime as dt

from dotenv import load_dotenv
from alpaca.trading.client import TradingClient
from apscheduler.schedulers.blocking import BlockingScheduler

from settings import config
from models.return_model import MixtureReturnModel
from models.simulator import MonteCarloSimulator
from risk.var import VaRCalculator
from portfolio.allocator import Allocator
from data.market_data import get_price_bars
from trader.executor import submit_orders

load_dotenv() 

client = TradingClient(os.getenv("alpaca_key"), os.getenv("alpaca_secret"), paper=True)

TICKERS = [ticker for sleeve_list in config.TICKERS.values() for ticker in sleeve_list] # type: ignore

# SCHED = BlockingScheduler()
# @SCHED.scheduled_job("cron", hour=20, minute=0) # After market close
def daily_rebalance():
    end = dt.date.today()
    start = end - dt.timedelta(days=365)
    prices = get_price_bars(TICKERS, start, end)
    returns = np.log(prices / prices.shift(1)).dropna() # type: ignore

    # 1. Fit multi‑modal model & simulate paths
    rm = MixtureReturnModel(n_components=4).fit(returns)
    sim = MonteCarloSimulator(rm)
    last_px = prices.iloc[-1]

    valid_symbols = last_px.dropna().index
    weights = (pd.Series(config.TARGET_WEIGHTS).reindex(valid_symbols).fillna(0)) # type: ignore
    last_px = last_px.loc[valid_symbols]

    paths = sim.simulate_prices(last_px.values, n_paths=5000, horizon=1)
    if paths.ndim == 2:
        paths = paths[:, None, :]   # now shape (n_paths, 1, n_assets)
    terminal_prices = paths[:, -1, :]     # works in both cases

    pnl = (terminal_prices - last_px.values) / last_px.values # relative P&L

    # 2. Risk metrics
    vc = VaRCalculator(config.VAR_CI) # type: ignore
    var = vc.mc_var(pnl @ np.ones(len(TICKERS)))
    print(f"1-day VaR @ {config.VAR_CI:.0%}: {var:,.2f} USD") # type: ignore

    # 3. Optimise weights
    exp_ret = returns.mean()
    cov = returns.cov()

    alloc = Allocator(config.TICKERS) # type: ignore
    weights = alloc.optimise(exp_ret, cov, nav=1.0) # relative weights

    # 4. Execute adjustments (placeholder NAV = 100k)
    account = client.get_account()
    nav = float(account.portfolio_value) # type: ignore
    submit_orders(weights, last_px, nav=nav)

if __name__ == "__main__":
    daily_rebalance()

