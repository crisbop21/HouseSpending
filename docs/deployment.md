# Deployment

How to set up the app locally and on Streamlit Community Cloud.

## Local development

### 1. Python environment

Use Python 3.11 or newer. Either `uv` or the stdlib `venv` works.

With `venv`:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

With `uv`:

```bash
uv venv --python 3.11
source .venv/bin/activate
uv pip install -r requirements.txt
```

### 2. Secrets

All secrets live in Streamlit secrets, not in `.env`.

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml` and fill in:

- `supabase.url` and `supabase.anon_key` from your Supabase project's API settings
- `supabase.service_role_key` if you intend to run admin scripts (optional for the app itself)
- `anthropic.api_key` only required from Phase 2 onward

`.streamlit/secrets.toml` is gitignored. Never commit it.

### 3. Run

```bash
streamlit run streamlit_app.py
```

Open http://localhost:8501.

## Streamlit Community Cloud

1. Push the repo to GitHub.
2. Sign in to https://share.streamlit.io with the GitHub account that owns the repo.
3. Click "New app", pick the repo and branch, set the main file to `streamlit_app.py`.
4. Open the app's settings, go to the **Secrets** tab, and paste the contents of your local `.streamlit/secrets.toml`. Save.
5. Deploy.

To rotate a secret, edit it in the Streamlit Cloud Secrets tab and click Save. The app will restart automatically.

## Anthropic billing alert

Set a usage alert at SGD 10 per month in the Anthropic console under Billing. Phase 1 will not call the API; Phase 2 onward will. Expected steady state cost is under SGD 5 per month.

## Supabase setup

1. Create a free tier project at https://supabase.com.
2. Record the project URL and anon key from Settings > API.
3. Apply SQL migrations from `sql/` in numeric order via the SQL editor (Phase 1.A).
4. Create both user accounts in Authentication > Users (Phase 1.A.6).
