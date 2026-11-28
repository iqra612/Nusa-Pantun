"""PantunEngine: the single entry point used by the UI (see INTERFACE_CONTRACT.md)."""
import time

import numpy as np
import pandas as pd

from .embedder import load_embedder
from .lexicon import THEME_WORDS
from .preprocess import tokenize
from .ranker import LinearRanker, make_ranker
from .retrieval import Retriever
from .rhyme import rhyme_label, rhyme_score, split_lines, structure_score, syllables

FEATURE_LABELS = {
    "sem_lex": "Kesamaan makna (TF-IDF)",
    "sem_dense": "Kesamaan makna (embedding)",
    "char": "Padanan ejaan",
    "theme": "Padanan tema",
    "coverage": "Liputan kata kunci",
    "rhyme": "Kualiti rima",
    "structure": "Struktur suku kata",
}
WEAK_MATCH_PCT = 30


class PantunEngine:
    def __init__(self, df: pd.DataFrame, rel: pd.DataFrame | None = None, use_dense: bool = True):
        self.df = df.reset_index(drop=True)
        self.embedder = load_embedder() if use_dense else None
        self.retriever = Retriever(self.df, self.embedder)
        self.lines = [split_lines(r.pembayang, r.maksud) for r in self.df.itertuples()]
        self.rhyme = np.array([rhyme_score(l) for l in self.lines])
        self.structure = np.array([structure_score(l) for l in self.lines])
        self.names = self.retriever.names + ["rhyme", "structure"]
        self.ranker = LinearRanker(self.names).fit(self._background())
        if rel is not None and len(rel):
            self.fit(rel)

    # ---- features -------------------------------------------------------
    def features(self, query: str):
        X, info = self.retriever.features(query)
        return np.column_stack([X, self.rhyme, self.structure]), info

    def _background(self):
        """Generic queries (one per theme) used as the linear ranker's SHAP baseline."""
        rows = [self.features(" ".join(w.split()[:3]))[0] for w in THEME_WORDS.values()]
        return np.vstack(rows)

    def fit(self, rel: pd.DataFrame):
        """Train the ranker. rel columns: query, pantun_id, relevance (0-2); unlabelled pairs count as 0."""
        id_to_row = {pid: i for i, pid in enumerate(self.df["id"])}
        Xs, ys = [], []
        for q, grp in rel.groupby("query"):
            X, _ = self.features(q)
            y = np.zeros(len(self.df))
            for pid, r in zip(grp["pantun_id"], grp["relevance"]):
                if pid in id_to_row:
                    y[id_to_row[pid]] = r
            Xs.append(X)
            ys.append(y)
        if Xs:
            self.ranker = make_ranker(self.names, np.vstack(Xs), np.concatenate(ys))
        return self

    def score_all(self, query: str) -> np.ndarray:
        X, _ = self.features(query)
        return self.ranker.predict(X)

    # ---- search ---------------------------------------------------------
    def search(self, query: str, k: int = 5, tema: str | None = None, era: str | None = None) -> dict:
        t0 = time.perf_counter()
        tokens = tokenize(query)
        base = {"query": query, "tokens": tokens, "themes_detected": [], "results": [], "weak": False,
                "mode": self.mode()}
        if not tokens:
            return {**base, "latency_ms": 0.0, "error": "Tulis sekurang-kurangnya satu perkataan bermakna."}
        X, info = self.features(query)
        pred = self.ranker.predict(X)
        mask = np.ones(len(self.df), dtype=bool)
        if tema:
            mask &= np.array([tema in [t.strip() for t in str(s).split(",")] for s in self.df["tema"]])
        if era:
            mask &= (self.df["era"] == era).to_numpy()
        order = [i for i in np.argsort(-pred) if mask[i]][:k]
        base_val, phi = self.ranker.explain(X[order]) if order else (0.0, np.zeros((0, len(self.names))))
        results = []
        for rank, (i, ph) in enumerate(zip(order, phi), start=1):
            row = self.df.iloc[i]
            feats = [
                {"name": n, "label": FEATURE_LABELS[n], "value": float(X[i, j]), "shap_pct": float(ph[j] * 100)}
                for j, n in enumerate(self.names)
            ]
            results.append({
                "rank": rank, "id": int(row["id"]), "tajuk": row.get("tajuk", ""), "lines": self.lines[i],
                "pembayang": row["pembayang"], "maksud": row["maksud"], "makna": row.get("makna", ""),
                "tema": [t.strip() for t in str(row["tema"]).split(",") if t.strip()], "era": row.get("era", ""),
                "sumber": row.get("sumber", ""), "match_pct": int(round(float(pred[i]) * 100)),
                "rhyme_label": rhyme_label(self.rhyme[i]), "syllables": [syllables(l) for l in self.lines[i]],
                "explanation": {
                    "base_pct": base_val * 100,
                    "features": sorted(feats, key=lambda f: -abs(f["shap_pct"])),
                    "keywords": self.retriever.keyword_contributions(query, int(i)),
                },
            })
        weak = not results or results[0]["match_pct"] < WEAK_MATCH_PCT
        return {**base, "themes_detected": info["themes"], "results": results, "weak": weak,
                "latency_ms": (time.perf_counter() - t0) * 1000}

    def mode(self) -> dict:
        return {
            "semantic": "Sentence-BERT + TF-IDF" if self.embedder else "TF-IDF (tanpa embedding)",
            "ranker": "LightGBM + TreeSHAP" if self.ranker.kind == "lightgbm" else "Linear + SHAP tepat",
            "corpus": len(self.df),
        }
