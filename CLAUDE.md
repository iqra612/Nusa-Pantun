# CLAUDE.md — PIRS (Pantun Information Retrieval System)

Project context for Claude Code sessions. Read this before making changes.

## Project

- **Name:** PIRS — Khazanah Pantun Melayu
- **Client:** Nusa Digital Solutions Sdn. Bhd., for a university library
- **Goal:** A web-based semantic search repository for traditional Malay *pantun*. Users search with natural-language sentences, moods, emotions, or keywords (up to 500 characters) and get ranked pantun results, each with an Explainable AI explanation of why it matched.
- **Dataset:** 2,000+ pantun, curated and tagged through the Admin Portal.

## Tech stack

- Python
- Streamlit (web UI)
- PostgreSQL (database)
- Sentence-BERT (`sentence-transformers`) for semantic embeddings and retrieval
- LightGBM for relevance ranking
- SHAP for per-result feature contribution bars

## UI pages and theme

Theme: minimalist cream background with dark-green accents.

1. **Utama** (Home): natural-language search box and sample mood/intent suggestions.
2. **Carian Pantun** (Search Results): ranked cards showing match percentage, theme/era filters, *Maksud* (interpretation), SHAP feature contribution bar chart, and Save/Copy/Share buttons.
3. **Simpanan** (Saved Poems): bookmarked collection with theme/era filters and sorting.
4. **Tentang** and **Admin Portal**: role-based access control (RBAC) for uploading, curating, and tagging the pantun dataset.

## Domain notes

- A *pantun* is a traditional Malay quatrain.
- **Pembayang** (opening lines): imagery or a hint that sets up the verse. Usually the first two lines.
- **Maksud** (closing lines): the meaning the verse conveys. Usually the last two lines.
- Rhyme is typically a-b-a-b.
- Search should match on meaning (including *maksud*), not only on surface words in the *pembayang* imagery.

## Repository layout and team ownership

| Folder | Owner | Responsibility |
|---|---|---|
| `database/` | Muhaimin (Data Engineer & System Architect) | PostgreSQL schema, migrations, DB access layer |
| `ml_engine/` | Aidil Haqkim (Lead AI & ML Engineer) | Sentence-BERT embeddings, LightGBM ranking, SHAP explanations, `search_pantun()` |
| `ui/` | Muhammad Nabil (Full-Stack Developer & UI/UX) | Streamlit UI components, theme, shared widgets |
| `pages/` | Muhammad Nabil (Full-Stack Developer & UI/UX) | Streamlit multipage views (Utama, Carian Pantun, Simpanan, Tentang, Admin) |
| `data/` | Muhaimin (data) | Dataset files. Full datasets are git-ignored. |
| Root (`app.py`, `INTERFACE_CONTRACT.md`, `README.md`, `requirements.txt`) | Iqra Izz (Project Manager & Lead Systems Analyst) | Entry point, contracts, project docs |

Iqra Izz: project management and lead systems analysis.

### Boundaries

- Work inside your own module folder. Changes to another member's folder go through that member, or through a PR they review.
- Cross-module interfaces are defined in `INTERFACE_CONTRACT.md`. Treat it as the source of truth. Change it only through a PR that everyone affected reviews.
- Do not commit secrets. `.env` is git-ignored. Only `.env.example` is tracked.

## Interface summary

Full details are in `INTERFACE_CONTRACT.md`.

- **`pantuns` table** (PostgreSQL): owned by `database/`.
- **`search_pantun(query, filters, top_k) -> dict`**: owned by `ml_engine/`, called by `pages/` and `ui/`.

## Working conventions

- Branch from `main`. Use `feature/<module>-<short-description>` branch names.
- Never commit directly to `main`. Open a PR and get at least one review.
- Run the app with `streamlit run app.py` from the repository root.
- Keep dependencies in `requirements.txt`. Add to it in the same PR that needs the package.
- Environment variables are read from `.env` (see `.env.example`).
