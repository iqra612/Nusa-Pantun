# INTERFACE CONTRACT — PIRS

This document is the source of truth for interfaces between team modules.

- **Owner:** Iqra Izz (Project Manager & Lead Systems Analyst)
- **Schema implementer:** Muhaimin (`database/`)
- **Function implementer:** Aidil Haqkim (`ml_engine/`)
- **Consumers:** Muhammad Nabil (`ui/`, `pages/`)

**Change rule:** Any change to this file goes through a PR. All owners and consumers listed above must approve it before merging.

---

## 1. PostgreSQL `pantuns` table

Owned by `database/`. Schema is created by a migration script in `database/`.

```sql
CREATE TABLE pantuns (
    id            SERIAL PRIMARY KEY,
    pantun_code   VARCHAR(20)  UNIQUE NOT NULL,   -- e.g. 'PNT-000001'
    baris_1       TEXT         NOT NULL,           -- pembayang line 1
    baris_2       TEXT         NOT NULL,           -- pembayang line 2
    baris_3       TEXT         NOT NULL,           -- maksud line 1
    baris_4       TEXT         NOT NULL,           -- maksud line 2
    pembayang     TEXT         NOT NULL,           -- baris_1 || ' ' || baris_2 (denormalised for display)
    maksud        TEXT         NOT NULL,           -- baris_3 || ' ' || baris_4 (denormalised for display)
    full_text     TEXT         NOT NULL,           -- all four lines joined with newline
    tema          VARCHAR(100),                    -- theme / mood, e.g. 'cinta', 'kesedihan'
    zaman         VARCHAR(50),                     -- era, e.g. 'Klasik', 'Moden'
    tags          TEXT[]       NOT NULL DEFAULT '{}',
    sumber        TEXT,                            -- source reference
    is_verified   BOOLEAN      NOT NULL DEFAULT FALSE,  -- curated by Admin
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_pantuns_tema  ON pantuns (tema);
CREATE INDEX idx_pantuns_zaman ON pantuns (zaman);
CREATE INDEX idx_pantuns_tags  ON pantuns USING GIN (tags);
```

### Field rules

| Field | Rule |
|---|---|
| `pantun_code` | Unique, never reused. |
| `baris_1`–`baris_4` | Stored as written. No trailing punctuation normalisation. |
| `pembayang`, `maksud`, `full_text` | Derived from `baris_*`. Written by the database layer on insert and update. |
| `tema`, `zaman` | Values come from controlled lists managed in the Admin Portal. |
| `tags` | Lowercase, trimmed strings. |

---

## 2. `search_pantun()` function

Owned by `ml_engine/`. Module path: `ml_engine/search.py`.

```python
def search_pantun(
    query: str,
    filters: dict | None = None,
    top_k: int = 10,
) -> dict:
    ...
```

### 2.1 Input

| Parameter | Type | Required | Rules |
|---|---|---|---|
| `query` | `str` | yes | 1 to 500 characters after stripping whitespace. Natural-language sentence, mood, emotion, or keywords. |
| `filters` | `dict \| None` | no | Optional keys below. Unknown keys raise `ValueError`. |
| `filters["tema"]` | `str` | no | Exact match on `pantuns.tema`. |
| `filters["zaman"]` | `str` | no | Exact match on `pantuns.zaman`. |
| `filters["tags"]` | `list[str]` | no | Match pantun having all listed tags. |
| `top_k` | `int` | no | 1 to 50. Default 10. |

### 2.2 Output

Returns a plain `dict` (JSON-serialisable, no custom classes).

```python
{
    "query": "rindu pada kekasih",          # echoed, stripped
    "total_matches": 37,                    # candidates passing filters, before top_k
    "results": [
        {
            "rank": 1,                      # 1-based
            "pantun_id": 412,               # pantuns.id
            "pantun_code": "PNT-000412",
            "pembayang": "Pergi ke pasar membeli padi ...",
            "maksud": "Hati rindu tak terubat lagi ...",
            "full_text": "Pergi ke pasar ...\nMembeli padi ...\nHati rindu ...\nTak terubat lagi ...",
            "tema": "cinta",
            "zaman": "Klasik",
            "match_percent": 87.4,          # float, 0.0 to 100.0, rounded to 1 decimal
            "shap": [                       # feature contributions, sorted by abs(contribution) desc
                {"feature": "semantic_similarity", "contribution": 0.31},
                {"feature": "keyword_overlap",     "contribution": 0.12},
                {"feature": "theme_match",         "contribution": -0.04}
            ],
            "maksud_summary": "Rindu yang sukar diubati ...",   # may be None
        }
    ],
}
```

### 2.3 Output rules

- `results` is sorted by `rank` ascending, which is by `match_percent` descending.
- `match_percent` is derived from the LightGBM relevance score. The mapping is defined in `ml_engine/`.
- `shap` lists the top features only (maximum 5). Contributions are floats and may be negative.
- If there are no matches, `results` is `[]` and `total_matches` is `0`. This is not an error.

### 2.4 Errors

| Condition | Exception |
|---|---|
| `query` empty or longer than 500 characters | `ValueError` |
| Unknown key in `filters` | `ValueError` |
| `top_k` outside 1 to 50 | `ValueError` |
| Database unreachable | `ConnectionError` |
| Model artifact missing | `FileNotFoundError` |

---

## 3. Environment variables

Defined in `.env.example`. Read with `python-dotenv`.

| Variable | Used by |
|---|---|
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | `database/` |
| `SECRET_KEY` | `app.py` and `pages/` |

---

## 4. Version history

| Version | Date | Change | Approved by |
|---|---|---|---|
| 0.1 | 2026-11-20 | Initial draft | Iqra Izz |
