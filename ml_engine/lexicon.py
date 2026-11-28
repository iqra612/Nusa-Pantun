"""Theme lexicon: Malay words that signal each pantun theme (tema).

Extend this file (or load it from the database) as the corpus grows.
"""
from .preprocess import stem

THEME_WORDS = {
    "budi": "budi jasa hutang balas kebaikan baik tolong bantu hargai terima kasih menolong sumbangan",
    "guru": "guru pensyarah murid pelajar sekolah ajar didik mengajar ilmu jasa terima kasih",
    "ilmu": "ilmu belajar tuntut baca buku pandai pelajar universiti kolej tekun rajin peperiksaan",
    "keluarga": "ibu ayah bapa emak mak abah keluarga anak orang tua mama kampung adik kakak",
    "cinta": "cinta sayang kasih setia kekasih hati jodoh mencintai rindu",
    "rindu": "rindu rindukan jauh pulang kampung perantauan halaman terbayang",
    "persahabatan": "kawan sahabat rakan teman setia bersama susah senang baik",
    "usaha": "usaha rajin berjaya kejayaan gigih tekun kerja hasil penat sabar",
    "motivasi": "semangat bangkit tabah sedih gagal putus asa dugaan cabaran peperiksaan kecewa tekanan harapan kegagalan",
    "agama": "doa solat sembahyang tuhan allah iman takwa surau masjid syukur hidayah",
    "raya": "raya aidilfitri ketupat lemang ramadan puasa lebaran",
    "maaf": "maaf salah silap ampun memaafkan khilaf dendam",
    "jenaka": "lucu gelak jenaka kelakar ketawa bebel lambat bangun sarapan",
    "perpaduan": "bersatu perpaduan negara merdeka rakyat damai aman kaum bangsa malaysia",
    "alam": "alam sungai hutan sampah bersih pokok tanam hijau cemar laut sekitar",
    "perpisahan": "berpisah jumpa selamat tinggal pergi jauh harap bertemu umur panjang",
    "tahniah": "tahniah graduasi tamat lulus kejayaan anugerah konvokesyen syabas",
    "perkahwinan": "kahwin pengantin perkahwinan nikah majlis walimah bahagia kenduri pelamin",
}

THEME_STEMS = {t: {stem(w) for w in words.split()} for t, words in THEME_WORDS.items()}
THEMES = sorted(THEME_WORDS)
