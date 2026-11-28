"""Retrieval features: how well each pantun matches a query sentence."""
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

from .lexicon import THEME_STEMS, THEME_WORDS
from .preprocess import normalize, surface_map, tokenize


def _identity(tokens):
    return tokens


class Retriever:
    """Computes query-to-pantun similarity features (all scaled to roughly 0-1)."""

    def __init__(self, docs: pd.DataFrame, embedder=None):
        self.docs = docs.reset_index(drop=True)
        self.embedder = embedder
        themes = [[t.strip() for t in str(s).split(",") if t.strip()] for s in self.docs["tema"]]
        self.doc_themes = themes
        texts = []
        for r, th in zip(self.docs.itertuples(), themes):
            theme_text = " ".join(THEME_WORDS.get(t, "") for t in th)
            texts.append(f"{r.maksud} {r.maksud} {r.pembayang} {theme_text}")
        self.doc_tokens = [tokenize(t) for t in texts]
        self.doc_sets = [set(t) for t in self.doc_tokens]
        self.word_vec = TfidfVectorizer(analyzer=_identity, sublinear_tf=True)
        self.word_mat = self.word_vec.fit_transform(self.doc_tokens)
        plain = [normalize(f"{r.pembayang} {r.maksud}") for r in self.docs.itertuples()]
        self.char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True)
        self.char_mat = self.char_vec.fit_transform(plain)
        self.dense = None
        if embedder is not None:
            self.dense = embedder.encode_cached([f"{r.maksud}. {r.pembayang}" for r in self.docs.itertuples()])
        self.names = ["sem_lex"] + (["sem_dense"] if self.dense is not None else []) + ["char", "theme", "coverage"]

    def theme_scores(self, tokens: list[str]) -> dict[str, float]:
        q = set(tokens)
        return {t: min(1.0, len(q & stems) / 2) for t, stems in THEME_STEMS.items()}

    def features(self, query: str):
        """Return (X [n_docs x n_features], info dict)."""
        tokens = tokenize(query)
        n = len(self.docs)
        qvec = self.word_vec.transform([tokens])
        sem_lex = np.clip(linear_kernel(qvec, self.word_mat).ravel() / 0.5, 0, 1)
        cols = [sem_lex]
        if self.dense is not None:
            qd = self.embedder.encode([query])
            cols.append(np.clip((self.dense @ qd[0] - 0.2) / 0.6, 0, 1))
        qc = self.char_vec.transform([normalize(query)])
        cols.append(np.clip((linear_kernel(qc, self.char_mat).ravel() - 0.1) / 0.4, 0, 1))
        ts = self.theme_scores(tokens)
        cols.append(np.array([max([ts.get(t, 0.0) for t in th] or [0.0]) for th in self.doc_themes]))
        qset = set(tokens)
        cols.append(np.array([len(qset & s) / len(qset) if qset else 0.0 for s in self.doc_sets]))
        ranked = sorted(ts.items(), key=lambda kv: -kv[1])
        info = {"tokens": tokens, "themes": [t for t, v in ranked if v > 0][:3]}
        return np.column_stack(cols) if n else np.zeros((0, len(cols))), info

    def keyword_contributions(self, query: str, doc_idx: int, top: int = 5) -> list[dict]:
        """Leave-one-out (occlusion): how much does each query word contribute to the TF-IDF match?"""
        tokens = tokenize(query)
        uniq = list(dict.fromkeys(tokens))
        if not uniq:
            return []
        names = surface_map(query)
        row = self.word_mat[doc_idx]
        full = float(linear_kernel(self.word_vec.transform([tokens]), row)[0, 0])
        drops = {}
        for s in uniq:
            rest = [t for t in tokens if t != s]
            part = float(linear_kernel(self.word_vec.transform([rest]), row)[0, 0]) if rest else 0.0
            drops[s] = max(0.0, full - part)
        total = sum(drops.values())
        if total <= 0:
            present = [s for s in uniq if s in self.doc_sets[doc_idx]]
            drops = {s: 1.0 for s in present}
            total = float(len(present))
        if total <= 0:
            return []
        out = [{"word": names.get(s, s), "share": v / total} for s, v in drops.items() if v > 0]
        return sorted(out, key=lambda d: -d["share"])[:top]
