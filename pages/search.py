"""Carian Pantun: structured metadata and readable verse display."""
import math
import re
import urllib.parse
from html import escape

import streamlit as st
from ui import components as C
from ui import state as S


def clean_text(value, default=""):
    if value is None:
        return default
    text = str(value).strip()
    return default if text.lower() in ("", "nan", "none", "<na>", "nat") else text


def themes(value):
    if isinstance(value, (list, tuple, set)):
        return list(dict.fromkeys(clean_text(v) for v in value if clean_text(v)))
    return [clean_text(value)] if clean_text(value) else []


def explicit_lines(value):
    if isinstance(value, (list, tuple)):
        return [line for part in value for line in explicit_lines(part)]
    text = clean_text(value)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = text.replace("\\r\\n", "\n").replace("\\n", "\n")
    text = re.sub(r"\s+[|/]\s*", "\n", text)
    return [line.strip() for line in text.splitlines() if line.strip()]


def punctuation_lines(line):
    # Keep the original punctuation; do not split trailing punctuation.
    return [p.strip() for p in re.split(r"(?<=[,;])\s+(?=\S)", line) if p.strip()]


def verse_lines(record):
    """Prefer explicit verse breaks; infer balanced compact halves for display."""
    p = explicit_lines(record.get("pembayang"))
    m = explicit_lines(record.get("maksud"))
    if len(p) == len(m) == 1:
        pp, mm = punctuation_lines(p[0]), punctuation_lines(m[0])
        if len(pp) == len(mm) and 2 <= len(pp) <= 6:
            p, m = pp, mm
    elif len(p) == 1 and len(m) > 1:
        pp = punctuation_lines(p[0])
        if len(pp) == len(m):
            p = pp
    elif len(m) == 1 and len(p) > 1:
        mm = punctuation_lines(m[0])
        if len(mm) == len(p):
            m = mm
    return p + m


def render_verse(record):
    lines = verse_lines(record)
    body = "<br>".join(escape(line) for line in lines)
    st.markdown(
        '<div style="line-height:1.85; font-size:1.05rem; padding:0.5rem 0;">'
        + body + '</div>', unsafe_allow_html=True,
    )


def percentage(record):
    try:
        v = float(record.get("match_pct", 0))
        return max(0.0, min(100.0, v)) if math.isfinite(v) else 0.0
    except (ValueError, TypeError):
        return 0.0


def render_score(record, bar=False):
    pct = percentage(record)
    st.markdown(f"**{pct:.0f}%**")
    st.caption("Padanan")
    if bar:
        st.progress(pct / 100)


def render_theme(record):
    value = ", ".join(themes(record.get("tema")))
    if value:
        st.caption(f"Tema: {value}")


def share_text(record):
    title = clean_text(record.get("tajuk"), "Pantun")
    source = clean_text(record.get("sumber"))
    return title + "\n\n" + "\n".join(verse_lines(record)) + (
        f"\n\nSumber: {source}" if source else ""
    )

st.title("Carian Pantun")
st.caption("Cari pantun berdasarkan ayat, perasaan atau maksud anda.")

with st.form("search_form", border=False):
    c1, c2 = st.columns([5, 1], vertical_alignment="bottom")
    q = c1.text_input(
        "Ayat carian", value=st.session_state.get("query", ""), max_chars=500,
        placeholder="Contoh: Saya berasa sedih kerana gagal dalam peperiksaan",
        label_visibility="collapsed",
    )
    go = c2.form_submit_button("Cari", type="primary", width="stretch")

if go:
    if not q.strip():
        st.warning("Tulis ayat carian dahulu.")
        st.stop()
    with st.spinner("Sedang mencari pantun..."):
        S.run_search(q.strip())
    st.session_state["sel_uid"] = 0

result = st.session_state.get("result")
if not result:
    st.info("Belum ada carian. Tulis satu ayat di atas untuk melihat pantun yang sepadan.")
    st.stop()
if result.get("error"):
    st.warning(result["error"])
    st.stop()

results = result.get("results", [])
for n, r in enumerate(results):
    r["_uid"] = n  # unik bagi setiap hasil, tidak bergantung pada nilai id
f1, f2, f3 = st.columns(3)
all_themes = sorted({t for r in results for t in themes(r.get("tema"))})
all_eras = sorted({clean_text(r.get("era"), "Tidak dinyatakan") for r in results})
tema = f1.selectbox("Tema", ["Semua tema"] + all_themes)
era = f2.selectbox("Era", ["Semua era"] + all_eras)
order = f3.selectbox("Susunan", ["Padanan tertinggi", "Padanan terendah"])
shown = [r for r in results if
         (tema == "Semua tema" or tema in themes(r.get("tema"))) and
         (era == "Semua era" or clean_text(r.get("era"), "Tidak dinyatakan") == era)]
shown = sorted(shown, key=percentage, reverse=order == "Padanan tertinggi")[:10]

st.caption(f'Hasil untuk {clean_text(result.get("query"), q)}. '
           f'{len(shown)} pantun dipaparkan dalam {float(result.get("latency_ms") or 0):.0f} ms.')
detected = themes(result.get("themes_detected"))
if detected:
    st.caption("Tema dikesan: " + ", ".join(detected))
if result.get("weak"):
    st.info("Tiada padanan yang kuat. Cuba ayat yang lebih lengkap, misalnya perasaan dan sebabnya.")
if not shown:
    st.info("Tiada pantun untuk penapis ini. Tukar tema atau era di atas.")
    st.stop()

def pilih(uid):
    st.session_state["sel_uid"] = uid


sel = st.session_state.get("sel_uid", 0)
rec = next((r for r in shown if r["_uid"] == sel), shown[0])
left, right = st.columns([1.1, 1], gap="large")

with left:
    st.subheader("Hasil carian")
    for i, r in enumerate(shown, 1):
        with st.container(border=True, key=f"card-{r['_uid']}{'-sel' if r['_uid'] == rec['_uid'] else ''}"):
            a, b = st.columns([4, 1])
            with a:
                st.markdown(f"**#{i} {escape(clean_text(r.get('tajuk'), 'Pantun'))}**")
                render_theme(r)
            with b:
                render_score(r)
            render_verse(r)
            source = clean_text(r.get("sumber"))
            if source:
                st.caption(f"Sumber: {source}")
            st.button("Lihat penjelasan", key=f"view_{r['_uid']}",
                      on_click=pilih, args=(r["_uid"],))
with right:
    st.subheader("Butiran pantun")
    with st.container(border=True, key="card-detail"):
        a, b = st.columns([4, 1])
        with a:
            st.markdown(f"**{escape(clean_text(rec.get('tajuk'), 'Pantun'))}**")
            render_theme(rec)
        with b:
            render_score(rec)
        render_verse(rec)
        source = clean_text(rec.get("sumber"))
        era_value = clean_text(rec.get("era"))
        if source:
            st.caption(f"Sumber: {source}")
        if era_value and era_value.lower() != "tidak dinyatakan":
            st.caption(f"Era: {era_value}")
        meaning = clean_text(rec.get("makna"))
        if meaning:
            st.markdown("**Makna pantun**")
            st.write(meaning)
        # Avoid displaying analysis calculated on a different number of lines.
        syllables = rec.get("syllables")
        if syllables is not None and hasattr(syllables, "__len__") and len(syllables) == len(verse_lines(rec)):
            rhyme = clean_text(rec.get("rhyme_label"))
            if rhyme:
                st.caption(f"Rima: {rhyme}")
            if len(syllables):
                st.caption("Suku kata setiap baris: " + ", ".join(map(str, syllables)))
        else:
            st.caption("Analisis rima dan suku kata perlu disemak semula.")
        st.divider()
        explanation = rec.get("explanation")
        st.markdown("**Penjelasan padanan (SHAP)**")
        if explanation is not None:
            st.markdown(C.shap_html(explanation, percentage(rec)), unsafe_allow_html=True)
            st.markdown("**Kata kunci anda yang menyumbang**")
            st.markdown(C.keywords_html(explanation), unsafe_allow_html=True)
            st.caption("Penjelasan ini menunjukkan faktor yang mempengaruhi model, bukan penilaian sastera atau budaya. Rujuk pakar bahasa untuk makna yang tepat.")
        else:
            st.info("Penjelasan padanan belum tersedia.")
        saved = rec["id"] in S.saved_ids()
        b1, b2, b3 = st.columns(3)
        b1.button("Buang" if saved else "Simpan", key=f"save_{rec['id']}", width="stretch",
                  icon=":material/bookmark:", on_click=S.toggle_saved, args=(rec["id"],))
        with b2.popover("Salin", width="stretch", icon=":material/content_copy:"):
            st.code(share_text(rec), language=None)
        b3.link_button("Kongsi", "https://wa.me/?text=" + urllib.parse.quote(share_text(rec)),
                       width="stretch", icon=":material/share:")
        if explanation is not None:
            given = st.session_state.get("feedback_given", {})
            if rec["id"] in given:
                st.caption("Terima kasih atas maklum balas anda.")
            else:
                st.caption("Adakah penjelasan ini membantu?")
                y, n = st.columns(2)
                y.button("Ya", key=f"fy_{rec['id']}", width="stretch", on_click=S.send_feedback, args=(rec["id"], True))
