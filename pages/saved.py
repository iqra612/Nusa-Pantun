import pandas as pd
import streamlit as st

from ui import components as C
from ui import state as S

st.title("Pantun Disimpan")
ids = S.saved_ids()
records = {r["id"]: r for r in S.collection_records()}
rows = [records[i] for i in ids if i in records]
st.caption(f"{len(rows)} pantun")

if not rows:
    st.markdown(C.empty_state("Belum ada pantun disimpan", "Simpan pantun kegemaran anda daripada hasil carian atau koleksi."),
                unsafe_allow_html=True)
    if st.button("Terokai koleksi", type="primary"):
        st.switch_page("pages/collection.py")
    st.stop()

for r in rows:
    with st.container(border=True, key=f"card-s{r['id']}"):
        st.markdown(C.collection_card_html(r), unsafe_allow_html=True)
        st.button("Buang", key=f"rm_{r['id']}", icon=":material/delete:", on_click=S.toggle_saved, args=(r["id"],))

export = pd.DataFrame([{"tajuk": r["tajuk"], "pantun": " / ".join(r["lines"]), "tema": ", ".join(r["tema"])} for r in rows])
st.download_button("Muat turun simpanan (CSV)", export.to_csv(index=False).encode("utf-8"), "pantun_disimpan.csv", "text/csv")
st.caption("Simpanan hanya disimpan untuk sesi semasa. Muat turun untuk menyimpannya secara kekal.")
