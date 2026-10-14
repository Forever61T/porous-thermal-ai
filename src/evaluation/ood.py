"""Small diagnostic extension; independent implementation using sklearn.

Scores are warning indicators, not calibrated prediction intervals. Grouped
calibration is kept separate from fitting and testing. No test label enters a
scaler, distance reference, threshold or model fit. No hyperparameter search.
"""
import numpy as np
from sklearn.neighbors import NearestNeighbors
from sklearn.preprocessing import StandardScaler


class DistanceReference:
    def fit(self, x):
        self.scaler = StandardScaler().fit(x)
        self.neighbors = NearestNeighbors(n_neighbors=1).fit(self.scaler.transform(x))
        return self

    def score(self, x):
        return self.neighbors.kneighbors(self.scaler.transform(x))[0][:, 0]


def tree_spread(forest, x):
    # Trees are correlated: this spread is NOT an error bar or calibrated CI.
    values = np.asarray(x)
    return np.std([tree.predict(values) for tree in forest.estimators_], axis=0, ddof=1)


def calibration_threshold(scores, groups, quantile=.95):
    maxima = np.array([np.max(scores[np.asarray(groups) == g]) for g in np.unique(groups)])
    return float(np.quantile(maxima, quantile, method='higher'))
