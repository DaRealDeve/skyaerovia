# SkyAerovia

**Your way through the sky** — a student flight-assistance project with **Skye**, our chatbot.

Sky + Aero + Via: the sky's pathway.

## Current status

Starter Streamlit chat interface only. Gemini and flight search are not connected yet. This prototype does not issue tickets or process payments. Demo flights and statuses must be clearly marked simulated.

## Run locally

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows, activate with `.venv\Scripts\activate`.

## Team workflow

Seven members including the repository owner. Invite the other six using their GitHub usernames. Each member accepts their invitation, creates a branch for their work, and opens a pull request for review. Keep `app.py` as the entry point; import separate modules when useful.

Planned features: route/date search using SQLite sample data, cheapest-flight comparison, simulated status, curated travel FAQs, session context, missing-information prompts and graceful fallback.

## Gemini integration

New code should use Google's supported `google-genai` SDK. Copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and replace the placeholder locally. Read the key with `st.secrets["GEMINI_API_KEY"]` when implementing the Gemini client. Never commit a real key. SQLite is included with Python and needs no requirements entry.

## Deploy

1. Push working code to GitHub.
2. Sign in to Streamlit Community Cloud and connect GitHub.
3. Create an app using this repository, the `main` branch and `app.py`.
4. In Advanced settings, add `GEMINI_API_KEY = "your-key"` to Secrets when Gemini is connected.
5. Deploy and check the chat and reset flow.

This starter can run without an API key. Add the key only when AI integration is implemented. Pin tested dependency versions before final submission.
