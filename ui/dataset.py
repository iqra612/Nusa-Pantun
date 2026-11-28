"""Read every pantun file in data/Dataset and normalise it for browsing and theme filtering.

Works with different column layouts per file. Recognised columns (case-insensitive):
  pembayang, maksud | pantun/teks/text/rangkap | baris1..baris4 | tema/kategori/theme | tajuk | sumber | makna | era
"""
import hashlib
import re
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = next((p for p in (ROOT / "data" / "Dataset", ROOT / "data" / "dataset") if p.is_dir()),
                   ROOT / "data" / "Dataset")

ALIASES = {
    "tajuk": {"tajuk", "title", "judul", "nama"},
    "pembayang": {"pembayang"},
    "maksud": {"maksud"},
    "teks": {"pantun", "teks", "text", "rangkap", "verse", "puisi", "kandungan", "content", "isi"},
    "tema": {"tema", "theme", "themes", "kategori", "category", "topik", "topic", "tag", "tags", "label"},
    "era": {"era", "zaman", "period"},
    "sumber": {"sumber", "source", "rujukan", "buku", "book", "penulis", "pengarang", "author"},
    "makna": {"makna", "erti", "meaning", "tafsiran", "penjelasan", "explanation"},
}
_BREAK = re.compile(r"\s*(?:<br\s*/?>|\\r\\n|\\n|\r\n|\n|/+|\|)\s*", re.I)
_PUNCT = re.compile(r"(?<=[,;])\s+(?=\S)")
_LINECOL = re.compile(r"^(?:baris|line|b)(\d)$")


def clean(value) -> str:
    text = "" if value is None else str(value).strip()
    return "" if text.lower() in ("nan", "none", "<na>", "nat") else re.sub(r"[ \t]+", " ", text)


def split_verse(*parts) -> list[str]:
    """Turn pembayang/maksud/full text into display lines. No '/' is kept.

    Explicit breaks (newline, '/', '|', <br>) win. If that gives fewer than 4 lines, comma and semicolon
    boundaries are used, so 'a, b; / c, d!' becomes four lines.
    """
    pieces = [p.strip() for part in parts for p in _BREAK.split(clean(part)) if p.strip()]
    if len(pieces) >= 4:
        return pieces
    expanded = [q.strip() for p in pieces for q in _PUNCT.split(p) if q.strip()]
    return expanded if len(pieces) < len(expanded) <= 8 else pieces


def split_tema(value) -> list[str]:
    out = []
    for t in re.split(r"[,;/|]", clean(value)):
        t = t.strip()
        if t:
            out.append(t[:1].upper() + t[1:])
    return list(dict.fromkeys(out))


def _read(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        return pd.read_excel(path, dtype=str)
    last = None
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            head = path.open(encoding=enc).readline()
            sep = max(",;\t|", key=head.count)
            return pd.read_csv(path, dtype=str, sep=sep, encoding=enc, keep_default_na=False)
        except UnicodeDecodeError as exc:
            last = exc
    raise last or ValueError("tidak dapat dibaca")


def _map_columns(columns) -> dict:
    found, lines = {}, {}
    for col in columns:
        key = re.sub(r"[^a-z0-9]", "", str(col).lower())
        m = _LINECOL.match(key)
        if m:
            lines[int(m.group(1))] = col
            continue
        for field, names in ALIASES.items():
            if key in names and field not in found:
                found[field] = col
    if lines:
        found["baris"] = [lines[k] for k in sorted(lines)]
    return found


def _load(signature) -> tuple[list[dict], list[dict]]:
    records, report, seen = [], [], {}
    for path in sorted(DATASET_DIR.glob("*")) if DATASET_DIR.is_dir() else []:
        if path.suffix.lower() not in (".csv", ".tsv", ".txt", ".xlsx", ".xls"):
            continue
        info = {"fail": path.name, "baris": 0, "dipaparkan": 0, "ada_tema": False, "lajur": "", "ralat": ""}
        try:
            df = _read(path)
            cols = _map_columns(df.columns)
            info.update(baris=len(df), ada_tema="tema" in cols,
                        lajur=", ".join(f"{k}={v}" for k, v in cols.items() if k != "baris"))
            if not any(k in cols for k in ("pembayang", "maksud", "teks", "baris")):
                info["ralat"] = "Tiada lajur pantun (pembayang/maksud/pantun/baris1..)."
            else:
                for row in df.to_dict("records"):
                    if "baris" in cols:
                        lines = split_verse(*[row[c] for c in cols["baris"]])
                    else:
                        lines = split_verse(*[row[cols[k]] for k in ("pembayang", "maksud", "teks") if k in cols])
                    if not lines:
                        continue
                    uid = "d" + hashlib.sha1(" ".join(lines).casefold().encode()).hexdigest()[:10]
                    tema = split_tema(row[cols["tema"]]) if "tema" in cols else []
                    if uid in seen:  # same pantun in two files: merge themes
                        seen[uid]["tema"] = list(dict.fromkeys(seen[uid]["tema"] + tema))
                        continue
                    rec = {
                        "id": uid, "lines": lines, "tema": tema,
                        "tajuk": clean(row[cols["tajuk"]]) if "tajuk" in cols else "",
                        "makna": clean(row[cols["makna"]]) if "makna" in cols else "",
                        "era": clean(row[cols["era"]]) if "era" in cols else "",
                        "sumber": (clean(row[cols["sumber"]]) if "sumber" in cols else "") or path.stem,
                        "fail": path.stem,
                    }
                    seen[uid] = rec
                    records.append(rec)
                    info["dipaparkan"] += 1
        except Exception as exc:  # one bad file must not hide the others
            info["ralat"] = f"{type(exc).__name__}: {exc}"
        report.append(info)
    return records, report


@st.cache_data(show_spinner="Membaca dataset...")
def _cached(signature):
    return _load(signature)


def load_dataset() -> tuple[list[dict], list[dict]]:
    """Return (records, per-file report). Cached; re-read automatically when a file changes."""
    files = sorted(DATASET_DIR.glob("*")) if DATASET_DIR.is_dir() else []
    return _cached(tuple((p.name, p.stat().st_mtime_ns) for p in files))


def verse_html(lines: list[str]) -> str:
    """First half italic (pembayang), second half normal (maksud); one line each, no slashes."""
    from html import escape

    half = len(lines) // 2 if len(lines) > 1 else len(lines)
    pb = "<br>".join(escape(l) for l in lines[:half])
    mk = "<br>".join(escape(l) for l in lines[half:])
    return f'<div class="pbody"><span class="pb">{pb}</span><span class="mk">{mk}</span></div>'
