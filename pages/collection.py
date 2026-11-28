from html import escape

import pandas as pd
import streamlit as st

from ui import components as C
from ui import dataset as D
from ui import state as S

PAGE_SIZE = 10
st.title("Koleksi Pantun")
st.caption("Semua pantun daripada fail dalam folder data/Dataset.")

records, report = D.load_dataset()
if not records:
    st.markdown(C.empty_state("Tiada pantun dijumpai",
                              f"Letakkan fail CSV dalam {D.DATASET_DIR} (lajur pembayang dan maksud, atau pantun)."),
                unsafe_allow_html=True)
    st.stop()

# Theme options come only from records that have a theme column value.
counts: dict[str, int] = {}
labels: dict[str, str] = {}
for r in records:
    for t in r["tema"]:
        counts[t.casefold()] = counts.get(t.casefold(), 0) + 1
        labels.setdefault(t.casefold(), t)
with_tema = sum(1 for r in records if r["tema"])
theme_keys = sorted(counts, key=lambda k: labels[k].casefold())
options = ["Semua tema"] + [f"{labels[k]} ({counts[k]})" for k in theme_keys] + ["Tanpa tema"]
key_of = {f"{labels[k]} ({counts[k]})": k for k in theme_keys}

preset = st.session_state.pop("filter_tema", None)
preset_label = next((o for o, k in key_of.items() if preset and k == str(preset).casefold()), None)

f1, f2, f3 = st.columns([2, 1.3, 1.3])
text = f1.text_input("Cari dalam koleksi", placeholder="Cari perkataan")
tema = f2.selectbox("Tema", options, index=options.index(preset_label) if preset_label else 0)
sumbers = sorted({r["sumber"] for r in records})
sumber = f3.selectbox("Sumber", ["Semua sumber"] + sumbers)


def keep(r):
    if tema == "Tanpa tema":
        ok = not r["tema"]
    elif tema != "Semua tema":
        ok = key_of[tema] in [t.casefold() for t in r["tema"]]
    else:
        ok = True
    if sumber != "Semua sumber" and r["sumber"] != sumber:
        ok = False
    return ok and (not text or text.casefold() in " ".join(r["lines"] + [r["tajuk"], r["makna"]]).casefold())


rows = [r for r in records if keep(r)]
st.caption(f"{len(rows)} daripada {len(records)} pantun. {with_tema} pantun mempunyai tema; "
           f"{len(records) - with_tema} tiada maklumat tema.")
if not rows:
    st.markdown(C.empty_state("Tiada pantun sepadan", "Cuba tukar kata carian atau penapis."), unsafe_allow_html=True)
    st.stop()

pages = max(1, -(-len(rows) // PAGE_SIZE))
page = st.number_input("Halaman", 1, pages, 1) if pages > 1 else 1
saved = S.saved_ids()
cols = st.columns(2, gap="medium")
for i, r in enumerate(rows[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]):
    with cols[i % 2]:
        with st.container(border=True, key=f"card-c{r['id']}"):
            head = f'<div class="ptitle">{escape(r["tajuk"])}</div>' if r["tajuk"] else ""
            st.markdown(head + C.chips(r["tema"]) + D.verse_html(r["lines"]), unsafe_allow_html=True)
            st.caption(f"Sumber: {r['sumber']}")
            st.button("Buang dari simpanan" if r["id"] in saved else "Simpan", key=f"cs_{r['id']}",
                      icon=":material/bookmark:", on_click=S.toggle_saved, args=(r["id"],))

with st.expander("Fail dataset yang dibaca"):
    st.dataframe(pd.DataFrame(report), hide_index=True, width="stretch")
