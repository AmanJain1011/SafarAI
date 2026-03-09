# Contributing to SafarAI 🏜️

Thank you for your interest in contributing to **SafarAI — AI-Powered Rajasthan Travel Budget Planner**!
This guide explains our branch strategy, PR process, and commit conventions.

---

## Branch Strategy

| Branch | Purpose |
|--------|---------|
| `main` | Stable, production-ready code. Direct pushes are **not** allowed. |
| `aman-dev` | AmanJain1011's active development branch. |
| `yash-dev` | Yash12256's active development branch. |
| `feature/<name>` | Short-lived feature branches cut from `aman-dev` or `yash-dev`. |

### Workflow

```
feature/my-feature  ──► aman-dev / yash-dev  ──► main
```

1. Cut a feature branch from your personal dev branch:
   ```bash
   git checkout aman-dev
   git pull origin aman-dev
   git checkout -b feature/my-awesome-feature
   ```
2. Make your changes and commit (see conventions below).
3. Push your branch and open a **Pull Request** targeting `aman-dev` or `yash-dev`.
4. Once reviewed and approved, the feature branch is merged.
5. Periodically, `aman-dev` and `yash-dev` are merged into `main` after a joint review.

---

## Pull Request Process

1. **Title** — Use the imperative mood: *Add hotel fraud detection*, *Fix budget parser regex*.
2. **Description** — Explain *what* changed and *why*. Link related issues with `Fixes #<issue>`.
3. **Tests** — Add or update tests in `tests/`. All existing tests must pass.
4. **Review** — At least one approval is required before merging.
5. **Squash merge** — We squash commits when merging feature branches to keep history clean.

---

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short description>
```

| Type | When to use |
|------|------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `chore` | Maintenance (deps, CI, config) |
| `docs` | Documentation only |
| `refactor` | Code restructure, no behaviour change |
| `test` | Adding or fixing tests |
| `style` | Formatting, whitespace |

**Examples:**
```
feat(nlu): add Hindi budget extraction regex
fix(optimizer): handle empty hotels CSV gracefully
chore(ci): add weekly price refresh workflow
docs: update README setup instructions
```

---

## Code Style

- Python 3.11+.
- Follow [PEP 8](https://pep8.org/). Run `flake8` or `ruff` before submitting.
- Type hints are encouraged.
- Bilingual comments (Hindi + English) are welcome in scraper and core modules — see existing files for style.

---

## Setting Up Locally

```bash
git clone https://github.com/AmanJain1011/SafarAI.git
cd SafarAI
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm

cp .env.example .env          # Add your API keys to .env
streamlit run src/app.py
```

---

## Questions?

Open a [GitHub Issue](https://github.com/AmanJain1011/SafarAI/issues) or reach out to the contributors listed in the README.
