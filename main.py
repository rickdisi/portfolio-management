import datetime as dt, numpy as np, os
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler

from portfolio_management.settings import config
from portfolio_management.models.return_model import MixtureReturnModel
from portfolio_management.models.simulator import MonteCarloSimulator
from portfolio_management.risk.var import VaRCalculator
from portfolio_management.portfolio.allocator import Allocator
from portfolio_management.data.market_data import get_price_bars
from portfolio_management.trader.executor import submit_orders

from alpaca.trading.client import TradingClient

from dotenv import load_dotenv
load_dotenv() 

client = TradingClient(os.getenv("alpaca_key"), os.getenv("alpaca_secret"), paper=True)

TICKERS = config.FICC_TICKERS + config.EQUITY_TICKERS + config.ETF_TICKERS + config.CRYPTO_TICKERS # type: ignore

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
    tickers_by_sleeve = {
        "FICC": config.FICC_TICKERS, # type: ignore
        "EQUITY": config.EQUITY_TICKERS, # type: ignore
        "ETF": config.ETF_TICKERS, # type: ignore
        "CRYPTO": config.CRYPTO_TICKERS # type: ignore
    }
    alloc = Allocator(tickers_by_sleeve)
    weights = alloc.optimise(exp_ret, cov, nav=1.0) # relative weights

    # 4. Execute adjustments (placeholder NAV = 100k)
    account = client.get_account()
    nav = float(account.portfolio_value) # type: ignore
    submit_orders(weights, last_px, nav=nav)

if __name__ == "__main__":
    daily_rebalance()

