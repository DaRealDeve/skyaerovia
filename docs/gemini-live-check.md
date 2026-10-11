# Gemini connection and live test

Checked on 11 October 2026 from Tarun's computer.

- DNS resolves generativelanguage.googleapis.com.
- Verified HTTPS through the SDK's HTTP transport reaches Google's server.
- The unauthenticated connection check receives HTTP 403, which is expected
  without an API key. This does not prove Gemini authentication or generation.
- The combined suite runs 74 checks: 73 pass and one live test is skipped.
  Other AI calls use mocks; no real key is used.
- The 50-case fallback retest passes 50/50. The previous baseline was 43/50.
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

The actual Python files have now been reviewed. The fixes are submitted on a
branch created from main and included in the integration draft for retesting.
See docs/extractor-review.md. Live Gemini still awaits a replacement key.
