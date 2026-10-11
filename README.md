# SkyAerovia
**Your way through the sky** — a student flight-search assistant featuring **Skye**.

**Public demo: [Open SkyAerovia](https://skyaerovia.streamlit.app/)** — deployed and checked on 12 October 2026. The demo is public; the repository and API key remain private.

The app combines Richa's navy/blue interface, Ayman's Gemini extractor with keyword fallback, Sakshi's search logic and 60 simulated flights prepared by Tarun/Codex. It asks for missing details, retains travel preferences, filters by route/date/budget/stops and sorts by price or duration. Flight cards, the logo, loading feedback and a complete chat/filter reset are included. This demo cannot book tickets or process payments.

## Run locally
Use Python 3.12 from the project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows, create the environment with `py -m venv .venv` and activate it with `.venv\Scripts\activate`.

The app works without an API key using the keyword fallback. For Gemini, copy `.streamlit/secrets.toml.example` to the ignored `.streamlit/secrets.toml`, fill in the key privately and restart the app. Streamlit Cloud reads the same settings from its Secrets box. Do not commit or paste a real key into chat. `GEMINI_MODEL` is optional; Ayman verified `gemini-3.5-flash` with his private replacement key. Tarun saved the deployment key privately in Streamlit Secrets. Hosted acceptance checks and a Gemini-versus-keyword control passed on 12 October; see `docs/deployment-checks.md`.

## Flight data
`flights.json` contains 60 simulated flights for **12–18 October 2026**, covering Delhi, Mumbai, Bengaluru, Chennai, Hyderabad, Kolkata, Pune and Ahmedabad. Airline display names may refer to real carriers, but these schedules and fares are simulated and are not bookable offers.

Fields: `id, airline, from, to, date, departure, arrival, duration, stops, price`.
Times are HH:MM in IST; duration is integer minutes; price is integer INR; IDs are unique. Arrivals are on the departure date.

Before a later demo, regenerate the next seven days and commit the updated file:

```sh
python scripts/generate_flights.py
```

The hosted app reads the committed file and displays the date range. It does not refresh dates automatically. See `docs/flight-data.md`.

## Verification
```sh
python -m unittest discover -s tests -v
python scripts/run_chat_checks.py
python scripts/run_ui_chat_checks.py
```

Latest local result: **81 tests run, 80 passed, one real-key test skipped**. All **50/50** fixed-date conversation cases pass both through the integration adapter and the complete Streamlit UI. Tests cover search, extraction, validation, dataset values and dates, filters, follow-ups, reset and HTML escaping. The 50-case fixtures use 2026-10-11 intentionally; production uses today's IST date.

Ayman supplied a successful real Gemini test screenshot (`source=ai`) on 11 October and Tarun relayed old-key deletion confirmation. No real key was used in the local integration review. For a future key change, verify a local private key without accepting fallback as success:

```sh
python scripts/check_gemini.py --live
```

See `docs/testing-report.md`, `docs/ui-chat-report.md`, `docs/frontend-review.md` and `docs/gemini-live-check.md` for scope and limits.

## Deploy
Use repository **DaRealDeve/skyaerovia**, branch **main**, entry point **app.py**, Python **3.12**, and add the private key under Streamlit Cloud **Advanced settings → Secrets**. Follow `docs/deployment.md` for sign-in, permissions, settings and hosted acceptance checks. The public deployment and hosted acceptance are complete. See `docs/deployment-checks.md` for the dated evidence and its limits.

## Team
The team retains all seven members. Richa supplied the frontend, Sakshi the search module and Ayman the extractor. Tarun/Codex cover Yashvardhan's data, Ayush's QA/API-helper work and Shivam's report/deck/demo work. Contributions are documented without attributing our replacement work to those members.

After the technical checks, Tarun/Codex prepared an eight-page report, editable ten-slide presentation, app screenshots, captioned MP4 walkthrough and presentation script. See `docs/team-responsibilities.md`, `docs/how-it-works.md`, `docs/demo-script.md` and `docs/submission-notes.md`.

