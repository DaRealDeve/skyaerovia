# Gemini connection and live test

Checked on 11 October 2026 from Tarun's computer.

- DNS resolves generativelanguage.googleapis.com.
- Verified HTTPS through the SDK's HTTP transport reaches Google's server.
- The unauthenticated connection check receives HTTP 403, which is expected
  without an API key. This does not prove Gemini authentication or generation.
- All 33 automated search/integration/UI/checker tests pass. Live calls are
  mocked in those tests; no real key is used.
- The separate 50-case fallback baseline remains 43 passed / 7 failed until
  Ayman's updated extractor is received and tested.
- Live Gemini remains PENDING. Tarun confirmed the exposed key has not been
  replaced. No exposed key was used.

## Run from this branch's project folder

Use Python 3.12 with requirements.txt installed.

```sh
python scripts/check_gemini.py
```

This command tests DNS/HTTPS and sends no key or chat message.

After the key owner creates a replacement in Google AI Studio, save the new key
privately in GEMINI_API_KEY or .streamlit/secrets.toml. Do not send it in chat,
commit it, screenshot it or include it in any report. Disable the exposed key.
For an existing deployed app, replace its secret and verify the new key before
disabling the old one to avoid downtime. See Google's official guidance:
https://ai.google.dev/gemini-api/docs/api-key#security-and-secret-management

Then run:

```sh
python scripts/check_gemini.py --live
```

The live command loads the local key without printing it, calls the AI path
directly and checks Delhi to Mumbai on tomorrow's IST date. Keyword fallback
cannot make this test pass. Exit 0 means PASS, 1 means failure, 2 means a missing
key/pending live test. Provider exception bodies are not printed.

If the selected model is unavailable, set GEMINI_MODEL to a model verified as
available for the key's project. A connection PASS does not establish model
availability. Do not disable certificate verification to fix a network failure.

## Ayman's updated code

The attached handoff note reports 31 passing tests and one skipped live test.
The attachment contains a summary, not updated Python code. At the last GitHub
check, main and durranyayman2-patch-1 still contain the original extractor blob
def9be636282f5e638dff6833902ee25d264f73b, and no fixes PR was present.

Ayman must upload his updated extractor.py and tests/test_extractor.py on a
branch created from main and provide the fixes PR link. Review that exact code
before copying it into the integration. Its result.problems validation metadata
also needs an integration check, especially for an invalid/past date replacing
an already saved valid date. The handoff summary alone cannot verify that fix.
