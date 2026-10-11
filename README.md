# SkyAerovia
**Your way through the sky** — a student flight-assistance project featuring Skye.

## Current status
Sakshi's search module and Ayman's original extractor are merged into main.
This integration connects extraction, session context, validation and flight search.
The demo cannot book tickets or process payments. All flight results are simulated.

Pending team deliverables:
- Yashvardhan: root-level `flights.json` (60 flights, eight supported cities, next seven days).
- Richa: final navy/blue interface.
- Ayman: extractor compatibility fixes; live Gemini tests with Tarun and Codex.
- Tarun and Codex: Ayush's 50-case QA, bug report, live API checks and final end-to-end tests. Ayush remains a team member.
- Tarun and Codex: Shivam's report, deck, screenshots and demo. Shivam remains a team member.

## Run locally
Use Python 3.12. From the project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows use `py -m venv .venv` and `.venv\\Scripts\\activate`.

The app runs with the keyword fallback without an API key. When ready, copy
`.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` and set your key
locally. The app passes that secret to the current extractor through the environment.
Never upload a real key. Ayman's current client also accepts `GEMINI_MODEL` as an
environment variable; the model and live Gemini connection still need verification.

## Integration
`app.py` calls `prepare_request` in `integration.py`, which uses
`extract_request(message, today, context)`. Supplied fields are merged into session
state. The app asks for missing details and calls `search_flights` with named
arguments, a default price sort, and a boolean nonstop value.

The integration accepts the original extractor intent names and the agreed names
(`search`, `cheapest`, `help`, `unknown`) while Ayman updates his module. It
handles date-only fallback replies and rejects past dates, unsupported cities,
invalid budgets and unsupported departure sorting before search. Booking/status
requests receive the demo's help explanation.

Sidebar overrides are explicit; otherwise the preferences in the chat are used.
New chat clears conversation state and results. Missing data is shown as a setup
state, not as an empty search.

## Flight data contract
Supported cities: Delhi, Mumbai, Bengaluru, Chennai, Hyderabad, Kolkata, Pune, Ahmedabad.
`flights.json` is a list with fields:
`id, airline, from, to, date, departure, arrival, duration, stops, price`.
Use unique string IDs, YYYY-MM-DD dates, HH:MM times in IST, integer minutes,
integer stop counts and integer prices in INR. Routes must use different cities.
The app validates the file when loading it. Keep the demo dates current.

## Tests
```sh
python -m unittest discover -s tests -v
```
The combined suite runs 74 checks: 73 pass and one live Gemini test is skipped.
It covers search, extractor, integration, Streamlit interactions and the API checker. Tests deliberately
disable Gemini and use temporary simulated fixtures; they do not use API keys or
replace the team's dataset. Passing these checks does not verify the live Gemini API.

## Team workflow
Create a branch, upload your work, open a PR into main and wait for review.
Keep `app.py` as the entry point and import separate modules. Richa can update the
presentation while preserving the integration calls and session-state behavior.

## Deployment handoff
After the pending files and live API test are complete, deploy this repository's
main branch with `app.py` on Streamlit Community Cloud. Add `GEMINI_API_KEY` in
Streamlit Secrets. Test searches, missing details, filters, fallback and reset on the
deployed app before using it for the final demo.

## Conversational QA
Run `python scripts/run_chat_checks.py` for the 50 fixed-date fallback cases.
Initial result: 43 passed, 7 failed. See `docs/testing-report.md` for exact inputs,
expected values and actual results. The 26 unittest checks passed separately.
Live Gemini and final app/deployment acceptance remain pending.

## Extractor retest
The 50 offline conversational cases now pass 50/50 after Ayman's fixes and the
integration corrections. The earlier baseline was 43/50. See docs/extractor-review.md
and docs/testing-report.md. Live Gemini and full-app/deployment tests remain pending.
