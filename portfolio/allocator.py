import cvxpy as cp, numpy as np, pandas as pd
from portfolio_management.settings import config

class Allocator:
    def __init__(self, tickers_by_sleeve):
        self.tbs = tickers_by_sleeve

    def optimise(self, exp_ret, cov, nav):
        n = len(exp_ret)
        w = cp.Variable(n)
        risk = cp.quad_form(w, cov)
        ret = exp_ret.values @ w
        constraints = [cp.sum(w) == 1,
        w >= 0]

        # Sleeve constraints
        idx_map = {t: i for i, t in enumerate(exp_ret.index)}
        for sleeve, tw in config.TARGET_WEIGHTS.items(): # type: ignore
            idxs = [idx_map[t] for t in self.tbs[sleeve]]
            constraints += [cp.sum(w[idxs]) == tw]
            
        # Position limit
        constraints += [w <= config.MAX_POSITION_PER_TICKER] # type: ignore

        prob = cp.Problem(cp.Maximize(ret - 0.5 * risk), constraints)
        prob.solve()
        return pd.Series(w.value, index=exp_ret.index)