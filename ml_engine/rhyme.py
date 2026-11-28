"""Rule-based pantun structure checks: end rhyme (a-b-a-b) and syllable counts."""
import re

VOWELS = "aeiou"


def last_word(line: str) -> str:
    words = re.findall(r"[A-Za-z]+", line)
    return words[-1].lower() if words else ""


def rime(word: str) -> str:
    """From the last vowel to the end of the word ('belayar' -> 'ar')."""
    i = len(word) - 1
    while i >= 0 and word[i] not in VOWELS:
        i -= 1
    return word[i:] if i >= 0 else word


def pair_score(line_a: str, line_b: str) -> float:
    a, b = last_word(line_a), last_word(line_b)
    if not a or not b:
        return 0.0
    if rime(a) == rime(b):
        return 1.0 if a[-2:] == b[-2:] else 0.7
    return 0.0


def rhyme_score(lines: list[str]) -> float:
    """Average of the line 1-3 and line 2-4 end-rhyme scores (0-1)."""
    if len(lines) != 4:
        return 0.0
    return (pair_score(lines[0], lines[2]) + pair_score(lines[1], lines[3])) / 2


def rhyme_label(score: float) -> str:
    if score >= 0.95:
        return "Rima a-b-a-b"
    if score >= 0.5:
        return "Rima separa"
    return "Tiada rima"


def syllables(line: str) -> int:
    """Approximate Malay syllable count: one per vowel, diphthongs ai/au/oi at word end count once."""
    total = 0
    for w in re.findall(r"[a-z]+", line.lower()):
        c = sum(ch in VOWELS for ch in w)
        if re.search(r"(ai|au|oi)$", w):
            c -= 1
        total += max(1, c)
    return total


def structure_score(lines: list[str], lo: int = 8, hi: int = 12) -> float:
    if len(lines) != 4:
        return 0.0
    return sum(lo <= syllables(l) <= hi for l in lines) / 4


def check_pantun(lines: list[str]) -> dict:
    """Validation summary used by the admin page."""
    lines = [l.strip() for l in lines]
    rs = rhyme_score(lines)
    syl = [syllables(l) for l in lines]
    return {
        "complete": len(lines) == 4 and all(lines),
        "rhyme_score": rs,
        "rhyme_label": rhyme_label(rs),
        "syllables": syl,
        "structure_score": structure_score(lines),
    }


def split_lines(pembayang: str, maksud: str) -> list[str]:
    """Pantun is stored as 'baris 1 / baris 2' for pembayang and for maksud."""
    parts = [p.strip() for p in f"{pembayang} / {maksud}".split("/")]
    return [p for p in parts if p]
