"""Rankers that turn similarity features into a match score, with additive explanations.

LightGBMRanker + TreeSHAP is the main path. LinearRanker (exact linear SHAP) is the fallback when
LightGBM/SHAP are unavailable or there are too few labelled pairs.
Both predict "expected relevance" in 0-1 (shown as match %), and explain() returns
(base_value, contributions) so that base + sum(contributions) ~= prediction.
"""
import numpy as np

PRIOR = {"sem_lex": 0.30, "sem_dense": 0.30, "char": 0.08, "theme": 0.25, "coverage": 0.15, "rhyme": 0.06, "structure": 0.04}


class LinearRanker:
    kind = "linear"

    def __init__(self, names):
        w = np.array([PRIOR[n] for n in names], dtype=float)
        self.w = w / w.sum()
        self.mean_ = np.zeros(len(names))

    def fit(self, X, y=None):
        self.mean_ = X.mean(axis=0)
        return self

    def predict(self, X):
        return np.clip(X @ self.w, 0, 1)

    def explain(self, X):
        return float(self.mean_ @ self.w), (X - self.mean_) * self.w


class LightGBMRanker:
    kind = "lightgbm"

    def __init__(self, names):
        self.names = names
        self.model = None
        self._explainer = None

    def fit(self, X, y):
        import lightgbm as lgb

        self.model = lgb.LGBMRegressor(
            n_estimators=200, learning_rate=0.08, num_leaves=7, min_child_samples=4,
            subsample=0.9, subsample_freq=1, monotone_constraints=[1] * X.shape[1],
            random_state=7, verbose=-1,
        )
        self.model.fit(X, np.asarray(y) / 2.0)  # graded relevance 0-2 -> 0-1
        self._explainer = None
        return self

    def predict(self, X):
        return np.clip(self.model.predict(X), 0, 1)

    def explain(self, X):
        import shap

        if self._explainer is None:
            self._explainer = shap.TreeExplainer(self.model)
        phi = np.asarray(self._explainer.shap_values(X))
        return float(np.ravel(self._explainer.expected_value)[0]), phi


def make_ranker(names, X=None, y=None):
    """Train LightGBM when there is enough labelled data, else fall back to the linear ranker."""
    if X is not None and y is not None and int((np.asarray(y) > 0).sum()) >= 20:
        try:
            return LightGBMRanker(names).fit(X, y)
        except Exception:
            pass
    return LinearRanker(names).fit(X if X is not None else np.zeros((1, len(names))))
