"""HTML snippets for pantun cards, SHAP bars and chips. All user/corpus text is escaped."""
from html import escape


def chips(items, alt=False) -> str:
    cls = "chip alt" if alt else "chip"
    return "".join(f'<span class="{cls}">{escape(str(i))}</span>' for i in items)


def pantun_body(rec: dict) -> str:
    pb = " /<br>".join(escape(l) for l in rec["lines"][:2])
    mk = " /<br>".join(escape(l) for l in rec["lines"][2:])
    return f'<div class="pbody"><span class="pb">{pb}</span><span class="mk">{mk}</span></div>'


def card_html(rec: dict) -> str:
    meta = chips(rec["tema"]) + chips([rec["era"], rec["rhyme_label"]], alt=True)
    return (f'<div><span class="rank">#{rec["rank"]}</span><span class="ptitle">{escape(rec["tajuk"])}</span></div>'
            f'{meta}{pantun_body(rec)}')


def pct_html(pct: int) -> str:
    return f'<div class="pct">{pct}%<small>Padanan</small></div>'


def collection_card_html(rec: dict) -> str:
    return (f'<div class="ptitle">{escape(rec["tajuk"])}</div>{chips(rec["tema"])}{chips([rec["era"]], alt=True)}'
            f'{pantun_body(rec)}')


def makna_html(text: str) -> str:
    return f'<div class="makna"><b>Maksud</b><br>{escape(text)}</div>' if text else ""


def shap_html(expl: dict, match_pct: int) -> str:
    feats = [f for f in expl["features"] if abs(f["shap_pct"]) >= 0.05]
    top = max([abs(f["shap_pct"]) for f in feats] + [5.0])
    rows = []
    for f in feats:
        w = min(50.0, abs(f["shap_pct"]) / top * 50)
        left, cls = (50, "pos") if f["shap_pct"] >= 0 else (50 - w, "neg")
        rows.append(
            f'<div class="shap-row"><span class="shap-label">{escape(f["label"])}</span>'
            f'<div class="shap-track"><div class="shap-fill {cls}" style="left:{left:.1f}%;width:{w:.1f}%"></div></div>'
            f'<span class="shap-val">{f["shap_pct"]:+.1f}</span></div>'
        )
    head = (f'<p class="note">Purata pantun dalam koleksi: {expl["base_pct"]:.0f}%. '
            f'Faktor di bawah menambah atau mengurangkan padanan pantun ini kepada {match_pct}% '
            f'(mata peratusan, nilai SHAP).</p>')
    return head + "".join(rows)


def keywords_html(expl: dict) -> str:
    kws = expl.get("keywords") or []
    if not kws:
        return '<p class="note">Tiada perkataan dalam carian yang sepadan secara langsung dengan pantun ini.</p>'
    rows = "".join(
        f'<div class="kw-row"><span class="shap-label">{escape(k["word"])}</span>'
        f'<div class="kw-track"><div class="kw-fill" style="width:{k["share"] * 100:.0f}%"></div></div>'
        f'<span class="shap-val">{k["share"] * 100:.0f}%</span></div>' for k in kws
    )
    return rows


def empty_state(title: str, text: str) -> str:
    return f'<div class="empty"><span class="serif">{escape(title)}</span>{escape(text)}</div>'


def share_text(rec: dict) -> str:
    return "\n".join(rec["lines"]) + "\n\n(PIRS, Khazanah Pantun Melayu)"
