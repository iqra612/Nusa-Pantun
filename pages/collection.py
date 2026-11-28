import streamlit as st

from ml_engine.lexicon import THEMES
from ui import components as C
from ui import state as S

PAGE_SIZE = 8
st.title("Koleksi Pantun")
st.caption("Semua pantun yang telah disahkan dalam koleksi.")

records = S.collection_records()
preset = st.session_state.pop("filter_tema", None)
f1, f2, f3 = st.columns([2, 1, 1])
text = f1.text_input("Cari dalam koleksi", placeholder="Cari perkataan atau tajuk")
themes = ["Semua tema"] + THEMES
tema = f2.selectbox("Tema", themes, index=themes.index(preset) if preset in themes else 0, key="col_tema")
era = f3.selectbox("Era", ["Semua era"] + sorted({r["era"] for r in records}))

def keep(r):
    hay = (" ".join(r["lines"]) + " " + r["tajuk"] + " " + r["makna"]).lower()
    return ((tema == "Semua tema" or tema in r["tema"]) and (era == "Semua era" or r["era"] == era)
            and (not text or text.lower() in hay))

rows = [r for r in records if keep(r)]
if not rows:
    st.markdown(C.empty_state("Tiada pantun dijumpai", "Cuba tukar kata carian atau penapis."), unsafe_allow_html=True)
    st.stop()

pages = max(1, -(-len(rows) // PAGE_SIZE))
page = st.number_input("Halaman", 1, pages, 1) if pages > 1 else 1
st.caption(f"{len(rows)} pantun")
saved = S.saved_ids()
cols = st.columns(2, gap="medium")
for i, r in enumerate(rows[(page - 1) * PAGE_SIZE: page * PAGE_SIZE]):
    with cols[i % 2]:
        with st.container(border=True, key=f"card-c{r['id']}"):
            st.markdown(C.collection_card_html(r), unsafe_allow_html=True)
            st.button("Buang dari simpanan" if r["id"] in saved else "Simpan", key=f"cs_{r['id']}",
                      icon=":material/bookmark:", on_click=S.toggle_saved, args=(r["id"],))
