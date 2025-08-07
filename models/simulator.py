import numpy as np

class MonteCarloSimulator:
    def __init__(self, return_model):
        self.rm = return_model

    def simulate_prices(self, last_prices, n_paths=1000, horizon=1):
        rtns = self.rm.sample(n_paths, horizon)
        prices = last_prices[None, :] * np.exp(rtns.cumsum(axis=1))
        return prices # shape (n_paths, horizon, n_assets)
    
