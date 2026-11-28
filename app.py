"""PIRS: Pantun Information Retrieval System (entry point and navigation)."""
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="PIRS | Khazanah Pantun Melayu", page_icon=":material/auto_stories:", layout="wide")

from ui import theme  # noqa: E402  (must come after set_page_config)
from ui.state import get_engine  # noqa: E402

theme.inject_css()
theme.sidebar_brand(f"Prototaip. {get_engine().mode()['corpus']} pantun dalam koleksi.")

pages = {
    "": [
        st.Page("pages/home.py", title="Utama", icon=":material/home:", default=True),
        st.Page("pages/search.py", title="Carian Pantun", icon=":material/search:"),
        st.Page("pages/collection.py", title="Koleksi", icon=":material/menu_book:"),
        st.Page("pages/saved.py", title="Simpanan", icon=":material/bookmark:"),
        st.Page("pages/about.py", title="Tentang", icon=":material/info:"),
    ],
    "Pentadbir": [st.Page("pages/admin.py", title="Admin", icon=":material/lock:")],
}
st.navigation(pages).run()
