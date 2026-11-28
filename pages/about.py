import streamlit as st

from ui.state import get_engine

st.title("Tentang PIRS")
st.write("PIRS (Pantun Information Retrieval System) membantu pelajar, pensyarah dan penyelidik menemui pantun Melayu "
         "berdasarkan ayat yang menerangkan perasaan, pengalaman atau maksud mereka, dan menerangkan kenapa setiap pantun dipilih.")

st.subheader("Cara ia berfungsi")
st.markdown(
    "1. Ayat anda dibersihkan, dinormalkan dan dipecahkan kepada akar perkataan.\n"
    "2. Setiap pantun dibandingkan dari segi makna (maksud pantun diberi berat lebih), ejaan, tema dan liputan kata kunci.\n"
    "3. Kualiti rima (a-b-a-b) dan struktur suku kata turut dikira.\n"
    "4. Model LightGBM menyusun pantun dan memberi peratusan padanan.\n"
    "5. SHAP menunjukkan faktor yang menambah atau mengurangkan padanan setiap pantun."
)

m = get_engine().mode()
st.subheader("Status sistem")
st.table({"Perkara": ["Padanan makna", "Penyusun dan penjelasan", "Bilangan pantun"],
          "Nilai": [m["semantic"], m["ranker"], str(m["corpus"])]})

st.subheader("Had yang perlu diketahui")
st.markdown(
    "- Peratusan padanan ialah anggaran model, bukan ketepatan atau penilaian sastera.\n"
    "- Penjelasan SHAP menerangkan tingkah laku model, bukan makna budaya pantun.\n"
    "- Koleksi dan label relevansi dalam prototaip ini ialah data contoh. Gantikan dengan koleksi berlesen yang disahkan pakar bahasa.\n"
    "- Tiada maklumat peribadi pengguna disimpan. Hanya ayat carian, masa dan skor padanan dicatat untuk mengukur prestasi sistem."
)
