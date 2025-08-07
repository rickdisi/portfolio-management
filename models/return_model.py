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
        means = np.array(self.model.means_).flatten()
        covs = np.array(self.model.covariances_).flatten()
        weights = np.asarray(self.model.weights_, dtype=float)

        comp = np.random.choice(np.arange(weights.shape[0]), size=(n_paths, horizon), p=weights)
        draws = np.random.normal(means[comp], np.sqrt(covs[comp])) 
    
        return draws # shape (n_paths, horizon)

    def save(self, path):
        dump(self.model, path)
    
    @classmethod
    def load(cls, path):
        inst = cls()
        inst.model = load(path)
        return inst