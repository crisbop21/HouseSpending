# Couple Expense Tracker

A web app for two users to track expenses across 5 to 6 debit and credit cards in SGD and USD. Manual entry plus LLM based statement extraction, learned merchant categorization, and a couple level dashboard.

See `TECHNICAL_BRIEF.md` for the architecture and data model. See `IMPLEMENTATION_PLAN.md` for phasing and tasks.

## Quick start

### 1. Prerequisites

- Python 3.11 or newer
- A Supabase project (free tier is sufficient)
- An Anthropic API key (only needed from Phase 2 onward)

### 2. Install

```bash
git clone <this-repo>
cd HouseSpending
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure secrets

All secrets live in Streamlit secrets, never in `.env` and never in code.

Locally, copy the template and fill in your values:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Then edit `.streamlit/secrets.toml` with your Supabase URL, Supabase anon key, and Anthropic API key. The real `.streamlit/secrets.toml` is gitignored.

On Streamlit Community Cloud, paste the same contents into the app's Secrets tab in the dashboard.

### 4. Run

```bash
streamlit run streamlit_app.py
```

The app will be at http://localhost:8501.

## Project layout

```
streamlit_app.py        Entry point and dashboard
pages/                  Multi page Streamlit pages
src/                    Service layer (db, auth, extraction, categorization, etc)
sql/                    Ordered Postgres migrations
tests/                  Pytest suite
docs/                   Deployment notes and runbook
```

## Development

```bash
pytest               # run tests
ruff check .         # lint
ruff format .        # format
```

CI runs both on push.

## Deploy

See `docs/deployment.md`.
