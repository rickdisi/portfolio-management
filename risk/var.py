import numpy as np

class VaRCalculator:
    def __init__(self, confidence=0.95):
        self.cl = confidence

    def historical_var(self, pnl_series):
        return -np.percentile(pnl_series, (1 - self.cl) * 100)

    def mc_var(self, simulated_pnl):
        """simulated_pnl: array (n_paths,)"""
        return -np.percentile(simulated_pnl, (1 - self.cl) * 100)