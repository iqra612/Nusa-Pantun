import pandas as pd
import streamlit as st

from database import auth, db
from ml_engine.evaluate import cross_validate
from ml_engine.lexicon import THEMES
from ml_engine.rhyme import check_pantun, split_lines
from ui import state as S

st.title("Pentadbir")

if not auth.admin_configured():
    st.warning("Akses admin belum ditetapkan. Cipta cincangan kata laluan, kemudian letakkannya dalam fail .env "
               "sebagai PIRS_ADMIN_PASSWORD_HASH (dan PIRS_ADMIN_USER).")
    st.code('python -m database.auth "kata-laluan-anda"', language="bash")
    st.stop()

if not st.session_state.get("is_admin"):
    with st.form("login", border=True):
        user = st.text_input("Nama pengguna")
        pw = st.text_input("Kata laluan", type="password")
        if st.form_submit_button("Log masuk", type="primary"):
            if auth.check_admin(user, pw):
                st.session_state["is_admin"] = True
                st.rerun()
            else:
                st.error("Nama pengguna atau kata laluan tidak betul.")
    st.stop()

top = st.columns([5, 1])
top[0].caption("Anda log masuk sebagai pentadbir.")
if top[1].button("Log keluar"):
    st.session_state["is_admin"] = False
    st.rerun()

tab_add, tab_manage, tab_perf, tab_use = st.tabs(["Tambah pantun", "Urus data", "Prestasi", "Penggunaan"])

with tab_add:
    with st.form("add_pantun"):
        tajuk = st.text_input("Tajuk")
        lines = [st.text_input(f"Baris {i}") for i in range(1, 5)]
        makna = st.text_area("Maksud dalam bahasa mudah", height=80)
        c1, c2 = st.columns(2)
        tema = c1.multiselect("Tema", THEMES)
        era = c2.selectbox("Era", ["Tradisional", "Kontemporari"])
        sumber = st.text_input("Sumber")
        lesen = st.text_input("Lesen atau kebenaran")
        verified = st.checkbox("Disahkan oleh pakar bahasa")
        submitted = st.form_submit_button("Tambah pantun", type="primary")
    if submitted:
        chk = check_pantun(lines)
        if not chk["complete"] or not tajuk.strip():
            st.error("Isi tajuk dan keempat-empat baris.")
        else:
            db.add_pantun({"tajuk": tajuk, "pembayang": f"{lines[0]} / {lines[1]}", "maksud": f"{lines[2]} / {lines[3]}",
                           "makna": makna, "tema": ",".join(tema), "era": era, "sumber": sumber, "lesen": lesen}, verified)
            S.refresh_engine()
            st.success(f"Pantun ditambah. {chk['rhyme_label']}; suku kata {chk['syllables']}.")
            if chk["structure_score"] < 1 or chk["rhyme_score"] < 0.95:
                st.warning("Struktur tidak sepenuhnya mengikut pola a-b-a-b dan 8 hingga 12 suku kata. Semak semula.")

    st.subheader("Import CSV")
    st.caption("Lajur wajib: pembayang, maksud (gunakan ' / ' antara dua baris). Pilihan: tajuk, makna, tema, era, sumber, lesen.")
    up = st.file_uploader("Fail CSV", type="csv")
    if up is not None:
        try:
            df = pd.read_csv(up)
        except Exception as exc:
            st.error(f"Fail tidak dapat dibaca: {exc}")
            df = None
        if df is not None:
            if not {"pembayang", "maksud"} <= set(df.columns):
                st.error("Lajur pembayang dan maksud diperlukan.")
            else:
                chk = [check_pantun(split_lines(str(r.pembayang), str(r.maksud))) for r in df.itertuples()]
                prev = df.assign(rima=[c["rhyme_label"] for c in chk], suku_kata=[c["syllables"] for c in chk])
                st.dataframe(prev, width="stretch")
                if st.button("Import sebagai belum disahkan"):
                    n = db.bulk_add(df)
                    S.refresh_engine()
                    st.success(f"{n} pantun diimport. Sahkan di tab Urus data supaya muncul dalam carian.")

with tab_manage:
    full = db.load_pantun(verified_only=False)
    view = full[["id", "tajuk", "tema", "era", "sumber", "lesen", "verified"]].assign(delete=False)
    edited = st.data_editor(view, hide_index=True, width="stretch",
                            disabled=["id", "tajuk", "tema", "era", "sumber", "lesen"], key="manage_editor")
    st.caption("Hanya pantun yang disahkan muncul dalam carian dan koleksi.")
    if st.button("Simpan perubahan", type="primary"):
        db.apply_changes(edited[["id", "verified", "delete"]])
        S.refresh_engine()
        st.success("Perubahan disimpan dan indeks dibina semula.")
        st.rerun()
    if st.button("Bina semula indeks"):
        S.refresh_engine()
        st.success("Indeks akan dibina semula pada carian seterusnya.")

with tab_perf:
    st.write("Penilaian menggunakan pengesahan silang mengikut query: model dilatih pada sebahagian query dan diuji pada query "
             "yang tidak pernah dilihat. Garis dasar ialah kesamaan TF-IDF sahaja.")
    rel = S.load_relevance()
    if rel is None:
        st.info("Letakkan data/relevance_seed.csv (query_id, query, pantun_id, relevance 0-2) untuk menjalankan penilaian.")
    elif st.button("Jalankan penilaian"):
        with st.spinner("Menilai..."):
            res = cross_validate(db.load_pantun(), rel)
        st.table(pd.DataFrame({
            "Kaedah": ["TF-IDF sahaja (garis dasar)", "PIRS (LightGBM)"],
            f"Precision@{res['k']}": [res["baseline"]["precision"], res["model"]["precision"]],
            f"NDCG@{res['k']}": [res["baseline"]["ndcg"], res["model"]["ndcg"]],
        }).round(3))
        st.caption(f"{res['n_queries']} query. Label relevansi contoh dalam prototaip ini dibuat sendiri, jadi angka ini "
                   "bukan bukti prestasi. Gunakan label daripada pakar bahasa untuk laporan sebenar.")

with tab_use:
    s = db.usage_stats()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Jumlah carian", s["searches"])
    m2.metric(f"Carian berjaya (padanan teratas ≥ {db.SUCCESS_PCT:.0f}%)", s["successful"])
    m3.metric("Purata masa (ms)", f"{s['avg_latency_ms']:.0f}")
    m4.metric("Penjelasan membantu", "-" if s["helpful_rate"] is None else f"{s['helpful_rate'] * 100:.0f}%")
    if len(s["per_day"]):
        st.bar_chart(s["per_day"].set_index("day"))
    st.dataframe(s["log"].tail(200), width="stretch", hide_index=True)
    st.download_button("Muat turun log carian (CSV)", s["log"].to_csv(index=False).encode("utf-8"), "search_log.csv", "text/csv")
    st.caption("Log hanya menyimpan ayat carian, masa dan skor. Tiada pengenalan pengguna.")
