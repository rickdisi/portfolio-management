import pandas as pd, numpy as np
from sklearn.mixture import GaussianMixture
from joblib import dump, load

class MixtureReturnModel:
    """Fit a Gaussian Mixture on daily returns and draw samples."""
    def __init__(self, n_components=3, random_state=42):
        self.model = GaussianMixture(n_components=n_components, random_state=random_state)

    def fit(self, returns: pd.DataFrame):
        self.model.fit(returns.values)
        return self

    def sample(self, n_paths: int, horizon: int):
        """Generate synthetic return paths for MC simulation."""
        means = np.array(self.model.means_)
        covs = np.array(self.model.covariances_)
        weights = np.asarray(self.model.weights_, dtype=float)

        K, n_assets = means.shape
        comp = np.random.choice(K, size=n_paths, p=weights)
        out = np.zeros((n_paths, horizon, n_assets))
        for i, comp in enumerate(comp):
            # draws a single vector of length n_assets
            draw = np.random.multivariate_normal(
                mean=means[comp],    # 1D array of length n_assets
                cov=covs[comp]       # 2D array (n_assets × n_assets)
            )
            out[i, 0, :] = draw 

        return out # shape (n_paths, horizon, n_assets)

    def save(self, path):
        dump(self.model, path)
    
    @classmethod
    def load(cls, path):
        inst = cls()
        inst.model = load(path)
        return inst