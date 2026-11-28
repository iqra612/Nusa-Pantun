"""Cream and dark-green theme (see .streamlit/config.toml for the base colours)."""
from pathlib import Path

import streamlit as st

LOGO = Path(__file__).parent / "assets" / "logo.svg"

CSS = """
<style>
:root{--bg:#FAF6EE;--surface:#FFFDF8;--soft:#F1EBDD;--ink:#25302A;--muted:#7C7766;--line:#E6DDC9;
--green:#2F5D46;--green-soft:#E6EDE3;--gold:#B8923A;--neg:#A89F8A;
--serif:'Iowan Old Style','Palatino Linotype',Palatino,Georgia,serif;}
html,body,[data-testid="stAppViewContainer"]{background:var(--bg);color:var(--ink);}
[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1120px;padding-top:2.2rem;padding-bottom:4rem;}
[data-testid="stSidebar"]{background:var(--soft);border-right:1px solid var(--line);}
h1,h2,h3,.serif{font-family:var(--serif);color:var(--green);letter-spacing:-.01em;font-weight:600;}
.hero{text-align:center;padding:2.2rem 0 1.2rem;}
.hero h1{font-size:clamp(2.2rem,5vw,3.6rem);line-height:1.08;margin:0 0 .8rem;}
.hero p{color:var(--muted);max-width:34rem;margin:0 auto;font-size:1.05rem;}
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button,.stLinkButton>a{border-radius:10px;
border:1px solid var(--line);background:var(--surface);color:var(--ink);font-weight:500;}
.stButton>button:hover,.stLinkButton>a:hover{border-color:var(--green);color:var(--green);}
.stButton>button[kind="primary"],.stFormSubmitButton>button[kind="primaryFormSubmit"]{background:var(--green);
border-color:var(--green);color:#FAF6EE;}
.stButton>button[kind="primary"]:hover{background:#264C3A;color:#fff;}
.stButton>button:focus-visible,input:focus-visible,textarea:focus-visible{outline:2px solid var(--gold);outline-offset:2px;}
textarea,input[type="text"],input[type="password"],[data-baseweb="select"]>div{background:var(--surface)!important;
border-radius:10px!important;}
[class*="st-key-card-"]{background:var(--surface);border:1px solid var(--line);border-radius:12px;padding:.4rem .5rem;}
[class*="st-key-card-"][class*="-sel"]{border-color:var(--green);background:#F3F7F0;}
.ptitle{font-family:var(--serif);font-size:1.12rem;font-weight:600;color:var(--green);margin:0 0 .2rem;}
.pbody{font-family:var(--serif);line-height:1.65;margin:.2rem 0 .5rem;}
.pbody .pb{font-style:italic;color:#4B574F;}
.pbody .mk{display:block;margin-top:.35rem;}
.chip{display:inline-block;background:var(--green-soft);color:var(--green);border-radius:99px;padding:.05rem .65rem;
font-size:.78rem;margin:0 .3rem .3rem 0;}
.chip.alt{background:var(--soft);color:#5E594A;}
.pct{text-align:right;font-family:var(--serif);font-size:1.9rem;font-weight:700;color:var(--green);line-height:1;}
.pct small{display:block;font-family:inherit;font-size:.72rem;font-weight:400;color:var(--muted);margin-top:.2rem;}
.rank{display:inline-block;background:#F3E7C4;color:#7A5C14;border-radius:99px;padding:0 .55rem;font-size:.75rem;
margin-right:.5rem;}
.panel-title{font-family:var(--serif);font-size:1.05rem;color:var(--green);margin:.9rem 0 .2rem;font-weight:600;}
.note{color:var(--muted);font-size:.85rem;}
.makna{background:#F8F0E2;border-radius:10px;padding:.6rem .9rem;margin:.4rem 0;}
.shap-row{display:flex;align-items:center;gap:.6rem;margin:.28rem 0;font-size:.88rem;}
.shap-label{flex:0 0 9.5rem;}
.shap-track{position:relative;flex:1;height:10px;background:var(--soft);border-radius:99px;}
.shap-track:after{content:"";position:absolute;left:50%;top:-3px;bottom:-3px;width:1px;background:var(--neg);}
.shap-fill{position:absolute;top:0;bottom:0;border-radius:99px;}
.shap-fill.pos{background:var(--green);}.shap-fill.neg{background:var(--neg);}
.shap-val{flex:0 0 3.6rem;text-align:right;font-variant-numeric:tabular-nums;}
.kw-row{display:flex;align-items:center;gap:.6rem;margin:.25rem 0;font-size:.88rem;}
.kw-row .kw-track{flex:1;height:8px;background:var(--soft);border-radius:99px;}
.kw-row .kw-fill{height:100%;background:var(--gold);border-radius:99px;}
.empty{border:1px dashed var(--line);border-radius:14px;text-align:center;padding:2.5rem 1rem;color:var(--muted);}
.empty .serif{font-size:1.3rem;display:block;margin-bottom:.3rem;}
@media (max-width:640px){.shap-label{flex-basis:6.5rem;}.pct{font-size:1.5rem;}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important;}}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def sidebar_brand(info: str = "") -> None:
    if LOGO.exists():
        st.logo(str(LOGO))
    if info:
        st.sidebar.caption(info)
