"""Malay text preprocessing: normalisation, light stemming and stop-word removal."""
import re
import unicodedata

SLANG = {
    "xde": "tiada", "xleh": "tidak boleh", "tak": "tidak", "nak": "mahu", "dgn": "dengan",
    "utk": "untuk", "yg": "yang", "sy": "saya", "kpd": "kepada", "dah": "sudah", "kat": "di",
    "cikgu": "guru", "grad": "graduasi", "konvo": "konvokesyen", "x": "tidak",
}

STOP = set(
    "yang dan di ke dari untuk saya aku mahu hendak dengan pada itu ini ada akan lah kah pun juga "
    "atau kepada sebagai oleh kita kami awak anda dia mereka tidak amat sangat nya sudah telah "
    "sedang rasa berasa kerana sebab bila apabila jika kalau agar supaya lagi pula yang ialah adalah".split()
)

PREFIXES = ("meng", "meny", "peng", "peny", "mem", "men", "pem", "pen", "ber", "ter", "me", "pe", "di", "se", "ke")
SUFFIXES = ("kan", "nya", "lah", "kah", "an", "i")


def normalize(text: str) -> str:
    """Lower-case, strip punctuation and digits, expand common slang."""
    text = unicodedata.normalize("NFKC", text or "").lower()
    text = re.sub(r"[^a-z\s-]", " ", text).replace("-", " ")
    words = [SLANG.get(w, w) for w in text.split()]
    return " ".join(" ".join(words).split())


def stem(word: str) -> str:
    """Very light Malay stemmer (one prefix, one suffix). Consistent, not linguistically perfect."""
    if len(word) < 5:
        return word
    for p in PREFIXES:
        if word.startswith(p) and len(word) - len(p) >= 3:
            word = word[len(p):]
            break
    for s in SUFFIXES:
        if word.endswith(s) and len(word) - len(s) >= 3:
            word = word[: -len(s)]
            break
    return word


def tokenize(text: str) -> list[str]:
    """Normalised, stop-word-free stems."""
    return [stem(w) for w in normalize(text).split() if w not in STOP and len(w) > 2]


def surface_map(text: str) -> dict[str, str]:
    """Map each stem to the first original word that produced it (for display)."""
    out: dict[str, str] = {}
    for w in normalize(text).split():
        if w not in STOP and len(w) > 2:
            out.setdefault(stem(w), w)
    return out
