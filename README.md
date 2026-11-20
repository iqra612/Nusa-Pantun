# PIRS — Khazanah Pantun Melayu

**Pantun Information Retrieval System (PIRS)** is a web-based semantic search repository for traditional Malay *pantun*. Users search with natural-language sentences, moods, emotions, or keywords (up to 500 characters) and receive ranked pantun, each with an explanation of why it matched.

Built by Nusa Digital Solutions Sdn. Bhd. for a university library.

- **Stack:** Python, Streamlit, PostgreSQL, Sentence-BERT, LightGBM, SHAP
- **Context for AI sessions:** see [`CLAUDE.md`](CLAUDE.md)
- **Interfaces between modules:** see [`INTERFACE_CONTRACT.md`](INTERFACE_CONTRACT.md)

---

## Team and module ownership

| Member | Role | Owns |
|---|---|---|
| Iqra Izz | Project Manager & Lead Systems Analyst | Root files (`app.py`, `README.md`, `INTERFACE_CONTRACT.md`, `CLAUDE.md`, `requirements.txt`), project scope, sign-off on contract changes |
| Muhaimmin | Data Engineer & System Architect | `database/`, `data/` |
| Aidil Haqkim | Lead AI & Machine Learning Engineer | `ml_engine/` |
| Muhammad Nabil | Full-Stack Developer & UI/UX Specialist | `ui/`, `pages/` |

Work inside your own module. If you need something from another module, check `INTERFACE_CONTRACT.md` first. If it is not covered there, ask the owner or open a PR that changes the contract.

---

## Local setup

### Prerequisites

- Python 3.10 or newer
- PostgreSQL 14 or newer
- Git

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/iqra612/Nusa-Pantun.git
cd Nusa-Pantun

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your local environment file
cp .env.example .env            # Windows: copy .env.example .env
# Then edit .env with your local database credentials and a SECRET_KEY.

# 5. Start the app
streamlit run app.py
```

Notes:

- `sentence-transformers` installs PyTorch, which is a large download.
- Never commit `.env`. It is git-ignored. Only `.env.example` is tracked.
- Full datasets (`data/full_dataset*`) and model artifacts (`*.pkl`, `*.joblib`) are git-ignored. Get them from Muhaimmin or Aidil, not from Git.

---

## Git workflow

`main` is the protected, always-working branch. Nobody commits directly to it.

### Daily routine

```bash
# Start of day: update main
git checkout main
git pull origin main

# Start a feature branch for your task
git checkout -b feature/<module>-<short-description>
# Examples:
#   feature/database-create-pantuns-table
#   feature/ml-lightgbm-ranker
#   feature/ui-search-results-cards
#   feature/pages-saved-poems-filters

# Work, then commit in small steps
git add <files>
git commit -m "Short imperative summary"

# Push your branch
git push -u origin feature/<module>-<short-description>
```

Then open a Pull Request into `main` on GitHub.

### Rules

1. **One branch per task.** Name it `feature/<module>-<short-description>`.
2. **Never commit directly to `main`.**
3. **Keep PRs small.** Aim for one logical change per PR, ideally under 400 lines.
4. **Get at least one review.** Reviewers must be from another module when the change touches a shared interface.
5. **Interface changes need everyone affected to approve.** If a change touches `INTERFACE_CONTRACT.md`, tag every owner and consumer listed in it.
6. **Sync often.** Run `git pull origin main` (or rebase onto it) at least once a day to avoid large merge conflicts.
7. **Never commit secrets or data.** Do not commit `.env`, full datasets, or model files. Check `git status` before every commit.
8. **Keep `main` green.** The app must start with `streamlit run app.py` before a PR is merged.
9. **Delete merged branches** after the PR is merged.

### Commit messages

- Use the imperative mood: `Add pantuns table migration`, not `Added` or `Adds`.
- Keep the first line under 72 characters.
- Add a body when the reason for the change is not obvious.

---

## Project layout

```
Nusa-Pantun/
├── app.py                  # Streamlit entry point (Iqra)
├── CLAUDE.md               # AI session context
├── INTERFACE_CONTRACT.md   # Cross-module interface spec
├── README.md
├── requirements.txt
├── .env.example
├── database/               # PostgreSQL schema and access layer (Muhaimmin)
├── ml_engine/              # Embeddings, ranking, SHAP, search_pantun() (Aidil)
├── ui/                     # Shared Streamlit components and theme (Muhammad Nabil)
├── pages/                  # Streamlit pages (Muhammad Nabil)
└── data/                   # Dataset files; full datasets are git-ignored (Muhaimmin)
```
