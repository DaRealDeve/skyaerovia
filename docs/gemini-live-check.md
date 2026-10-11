# Gemini connection and live test

## Current status — 12 October 2026

Ayman supplied a terminal screenshot of a successful real Gemini test on 11 October: gemini-3.5-flash, source=ai, one test run, OK and no skipped test. Tarun relayed Ayman's confirmation that the old exposed key was deleted. The updated secrets-aware test is on GitHub.

The review uses the current IST date for live tests; deterministic offline tests keep their fixed reference date. With flight-data and final-frontend checks, the combined suite runs 81 tests: 80 pass and one real-key test is skipped on Tarun's review machine. All 50 offline conversation cases pass through both the adapter and the full Streamlit UI. Ayman's private key was not shared or reused.

The shared app's key is now stored privately in Streamlit Secrets. On the hosted app, a cleared conversation resolved "Fly from India's capital to Maharashtra's capital tomorrow for less than 5000 rupees" to Delhi → Mumbai on 2026-10-13, with three expected flights. The same message in the local keyword-only control did not produce a valid route. Since the current implementation has only Gemini and keyword extraction paths, this contrast supports the conclusion that hosted Gemini answered. This is an inference from controlled behavior, not a source=ai provider log. It does not mean all 50 cases were tested live. See deployment-checks.md.

## Connectivity previously checked on Tarun's computer

On 11 October DNS and verified HTTPS reached generativelanguage.googleapis.com. An unauthenticated HTTP 403 was expected. Connectivity alone does not establish authentication or generation.

## Run from the project folder

Use Python 3.12 with requirements.txt installed.

```sh
python scripts/check_gemini.py
```

The default command sends no key or chat message. Save the shared app's key privately as GEMINI_API_KEY in the environment or .streamlit/secrets.toml; never commit or paste it in chat. Then run:

```sh
python scripts/check_gemini.py --live
```

This calls the AI path directly and checks Delhi to Mumbai on tomorrow's IST date. Keyword fallback cannot count as PASS. Exit 0 means PASS, 1 failure and 2 missing key. No raw provider error body is printed. Set GEMINI_MODEL to a model available for this key's project if necessary. Keep HTTPS certificate verification enabled.

The standalone unittest live check also supports the local secrets file:

```sh
python -m unittest tests.test_extractor.TestLiveGemini -v
```

See docs/extractor-review.md for the evidence and its limits.

