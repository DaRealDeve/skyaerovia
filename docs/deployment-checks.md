# Hosted acceptance — 12 October 2026

Public demo: https://skyaerovia.streamlit.app/
Repository: DaRealDeve/skyaerovia (private), main, app.py. Python 3.12. Pinned dependencies: streamlit 1.65.0 and google-genai 2.29.0. Tarun saved the new API key privately in Streamlit Secrets; no credential appears in code, reports or screenshots.

Application code checked: main commit 9e1b1fa064d8ca2c10efcb9ed4735ab0847a2698. Later documentation-only updates do not change that application behavior.

| Check | Observed result |
|---|---|
| Welcome and branding | Logo, Skye, sidebar, chat and simulated-data/date-range labels visible |
| Delhi to Mumbai tomorrow under 5000 | On 12 October, tomorrow resolves to 2026-10-13; 3 choices at INR 3,200, 3,900 and 4,280 |
| Price sorting | 3,200, 3,900, 4,280 |
| Duration sorting | 130, 140, 265 minutes |
| Nonstop only | 2 choices |
| Nonstop and maximum INR 3,500 | 0 choices, with recovery guidance |
| Allow stops at INR 3,500 | 1 choice at INR 3,200 |
| Missing information | “from Delhi” asks for destination; “Mumbai” asks for date; “2026-10-13” completes search |
| Clear chat | Conversation and results removed; visible sort/stop controls return to Use chat preference and budget is disabled |
| Public access | Make this app public enabled with Tarun's explicit approval |

## Reset fix

The first hosted reset cleared saved request values but browser sidebar controls retained old choices. The fix explicitly assigns the default widget values. Five app tests passed after the change, and the hosted browser visibly returned to the defaults.

## Hosted Gemini evidence

In a cleared conversation, the request **“Fly from India's capital to Maharashtra's capital tomorrow for less than 5000 rupees”** produced Delhi → Mumbai on 2026-10-13 and the three expected flights.

The identical request in the local keyword-only control returned origin India and no destination, so it could not form a valid route. Since this build has only Gemini and keyword paths, the contrasting behavior supports the conclusion that the hosted AI path answered. This is a behavioral inference, not an observed source=ai provider log. It establishes that one semantic request worked, not broad natural-language accuracy.

## Separate offline evidence and limits

The combined local unittest suite previously ran 81 checks: 80 passed and one private-key test was skipped. All 50 deterministic conversation cases passed through both the adapter and full Streamlit UI with forced fallback. These are separate checks, not 50 live Gemini calls. Ayman also supplied one successful live-key test from his environment.

There is no GitHub CI workflow; these results came from local execution and manual hosted checks. No live flight-data service, booking, payments, seat inventory or flight status is included. The simulated committed schedule covers 12–18 October 2026 and must be refreshed and committed before a later demo.
