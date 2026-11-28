"""Shared engine and session state for all pages."""
import os
from pathlib import Path

import pandas as pd
import streamlit as st

from database import db
from ml_engine import PantunEngine

ROOT = Path(__file__).resolve().parents[1]
REL_CSV = ROOT / "data" / "relevance_seed.csv"


def load_relevance() -> pd.DataFrame | None:
    return pd.read_csv(REL_CSV) if REL_CSV.exists() else None


@st.cache_resource(show_spinner="Menyediakan enjin PIRS...")
def get_engine() -> PantunEngine:
    db.init_db()
    return PantunEngine(db.load_pantun(), load_relevance(), use_dense=os.getenv("PIRS_USE_DENSE", "1") != "0")


def refresh_engine() -> None:
    """Call after the admin changes the corpus so the index is rebuilt."""
    get_engine.clear()


def run_search(query: str, k: int = 20) -> dict:
    result = get_engine().search(query.strip(), k=k)
    sid = None
    if result["tokens"]:
        top = result["results"][0]["match_pct"] if result["results"] else 0
        sid = db.log_search(query, len(result["results"]), top, result["latency_ms"])
    st.session_state.update(
        query=query.strip(), result=result, search_id=sid,
        sel=result["results"][0]["id"] if result["results"] else None,
    )
    return result


def saved_ids() -> list[int]:
    return st.session_state.setdefault("saved", [])


def toggle_saved(pid: int) -> None:
    ids = saved_ids()
    ids.remove(pid) if pid in ids else ids.append(pid)


def select(pid: int) -> None:
    st.session_state["sel"] = pid


def send_feedback(pid: int, helpful: bool) -> None:
    db.log_feedback(st.session_state.get("search_id"), pid, helpful)
    st.session_state["feedback_given"] = {**st.session_state.get("feedback_given", {}), pid: helpful}


def collection_records() -> list[dict]:
    """All pantun in the index as display records (same shape as search results, without scores)."""
    from ml_engine.rhyme import rhyme_label, rhyme_score

    eng = get_engine()
    out = []
    for i, row in eng.df.iterrows():
        out.append({
            "id": int(row["id"]), "tajuk": row.get("tajuk", ""), "lines": eng.lines[i], "makna": row.get("makna", ""),
            "tema": [t.strip() for t in str(row["tema"]).split(",") if t.strip()], "era": row.get("era", ""),
            "sumber": row.get("sumber", ""), "rhyme_label": rhyme_label(rhyme_score(eng.lines[i])),
        })
    return out
