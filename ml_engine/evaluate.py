"""Offline evaluation: Precision@k and NDCG@k with query-grouped cross-validation."""
import numpy as np
import pandas as pd

from .pipeline import PantunEngine


def precision_at_k(rels, k=5):
    return float(np.mean(np.asarray(rels)[:k] > 0)) if len(rels) else 0.0


def ndcg_at_k(rels, ideal, k=5):
    def dcg(r):
        r = np.asarray(r, dtype=float)[:k]
        return float(np.sum(r / np.log2(np.arange(2, len(r) + 2))))
    best = dcg(sorted(ideal, reverse=True))
    return dcg(rels) / best if best > 0 else 0.0


def _eval_queries(engine, df, rel, queries, k):
    id_to_row = {pid: i for i, pid in enumerate(df["id"])}
    out = {"baseline": [], "model": []}
    for q in queries:
        grp = rel[rel["query"] == q]
        gains = np.zeros(len(df))
        for pid, r in zip(grp["pantun_id"], grp["relevance"]):
            gains[id_to_row[pid]] = r
        X, _ = engine.features(q)
        for key, score in (("baseline", X[:, 0]), ("model", engine.ranker.predict(X))):
            order = np.argsort(-score)
            r = gains[order]
            out[key].append((precision_at_k(r, k), ndcg_at_k(r, gains, k)))
    return out


def cross_validate(df: pd.DataFrame, rel: pd.DataFrame, n_splits: int = 4, k: int = 5, seed: int = 7, use_dense=False):
    """Train on some queries, test on held-out queries. Baseline = TF-IDF similarity only."""
    queries = np.array(sorted(rel["query"].unique()))
    rng = np.random.default_rng(seed)
    rng.shuffle(queries)
    folds = np.array_split(queries, n_splits)
    agg = {"baseline": [], "model": []}
    for i, test_q in enumerate(folds):
        train_q = np.concatenate([f for j, f in enumerate(folds) if j != i])
        engine = PantunEngine(df, rel[rel["query"].isin(train_q)], use_dense=use_dense)
        res = _eval_queries(engine, df, rel, list(test_q), k)
        for key in agg:
            agg[key] += res[key]
    return {
        "n_queries": int(len(queries)), "k": k,
        "baseline": {"precision": float(np.mean([a for a, _ in agg["baseline"]])), "ndcg": float(np.mean([b for _, b in agg["baseline"]]))},
        "model": {"precision": float(np.mean([a for a, _ in agg["model"]])), "ndcg": float(np.mean([b for _, b in agg["model"]]))},
    }
