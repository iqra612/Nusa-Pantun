import streamlit as st

from ml_engine.lexicon import THEMES
from ui import state as S

st.markdown(
    '<div class="hero"><h1>Setiap rasa,<br>ada pantunnya.</h1>'
    "<p>Tulis perasaan, pengalaman atau maksud anda dalam satu ayat. PIRS mencari pantun Melayu yang sepadan "
    "dan menerangkan kenapa pantun itu dipilih.</p></div>",
    unsafe_allow_html=True,
)


def search(q: str) -> None:
    if not q.strip():
        st.warning("Tulis satu ayat dahulu, contohnya perasaan atau maksud yang mahu anda sampaikan.")
        return
    S.run_search(q)
    st.switch_page("pages/search.py")


_, mid, _ = st.columns([1, 6, 1])
with mid:
    q = st.text_area("Ayat carian", height=110, max_chars=500, label_visibility="collapsed",
                     placeholder="Contoh: Saya berasa sedih kerana gagal dalam peperiksaan...", key="home_q")
    if st.button("Cari pantun", type="primary", width="stretch"):
        search(q)

    st.markdown('<p class="note" style="text-align:center;margin:1rem 0 .4rem">Cuba carian ini</p>', unsafe_allow_html=True)
    examples = ["Saya rindu seseorang", "Semangat untuk bangkit", "Menghargai jasa sahabat"]
    for col, text in zip(st.columns(len(examples)), examples):
        if col.button(text, key=f"ex_{text}", width="stretch"):
            search(text)

    st.markdown('<h3 style="margin-top:2.4rem">Terokai mengikut tema</h3>', unsafe_allow_html=True)
    featured = ["budi", "cinta", "rindu", "motivasi", "persahabatan", "raya"]
    for col, theme in zip(st.columns(len(featured)), featured):
        if col.button(theme.capitalize(), key=f"th_{theme}", width="stretch"):
            st.session_state["filter_tema"] = theme
            st.switch_page("pages/collection.py")
