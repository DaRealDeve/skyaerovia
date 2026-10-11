"""Check connectivity; add --live to test Gemini without any fallback.

No key is sent in the default connection check. Secrets stay local and are never
printed. Use a replacement key if the previous key was exposed in a chat.
"""
import argparse
import logging
import os
import socket
import sys
import tomllib
from datetime import datetime, timedelta, timezone
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
HOST = "generativelanguage.googleapis.com"
MESSAGE = "Delhi to Mumbai tomorrow"


def check_connection():
    try:
        socket.getaddrinfo(HOST, 443)
        response = httpx.get(f"https://{HOST}/v1beta/models", timeout=15)
    except (OSError, httpx.HTTPError) as error:
        print("Connection check failed:", type(error).__name__)
        print("Check internet access, DNS and any proxy; then retry.")
        return False
    if response.status_code not in (200, 400, 401, 403):
        print("Unexpected connection-check status:", response.status_code)
        return False
    print("Connection PASS: Google responded without an API key.")
    print("This proves connectivity, not that a key or Gemini model works.")
    return True


def load_local_key():
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if key:
        return key
    path = ROOT / ".streamlit" / "secrets.toml"
    if not path.exists():
        return None
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        print("Cannot read local secrets. Check the file's TOML format.")
        return None
    key = data.get("GEMINI_API_KEY")
    return key.strip() if isinstance(key, str) and key.strip() else None


def failure_hint(error):
    # Do not print raw exception messages: providers can echo request details.
    status = getattr(error, "code", None)
    if status is None:
        status = getattr(getattr(error, "response", None), "status_code", None)
    return {
        400: "Check the key and request/model configuration.",
        401: "The key was not accepted; check the replacement key.",
        403: "Check this key's project access and Gemini API restrictions.",
        404: "Check GEMINI_MODEL against the models available in AI Studio.",
        429: "Quota or rate limit reached; check quota and retry later.",
    }.get(status, "Check connection, model availability and API settings.")


def check_live(key):
    os.environ["GEMINI_API_KEY"] = key
    # Suppress SDK/extractor logs so an exception cannot echo a credential.
    previous_level = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    try:
        import extractor
        today = datetime.now(timezone(timedelta(hours=5, minutes=30))).date()
        # This calls the AI path directly. The fallback cannot mark this PASS.
        result = extractor.extract_with_ai(MESSAGE, today, {})
        expected = {"origin": "Delhi", "destination": "Mumbai",
                    "date": (today + timedelta(days=1)).isoformat()}
        if not isinstance(result, dict) or any(result.get(k) != v for k, v in expected.items()):
            print("Live Gemini FAIL: returned travel fields do not match the test.")
            return False
        if result.get("intent") not in ("search", "cheapest", "search_flights"):
            print("Live Gemini FAIL: returned intent is not a search.")
            return False
        print("Live Gemini PASS: AI path returned the correct route and tomorrow's date.")
        print("No keyword fallback was used. No key was printed.")
        return True
    except Exception as error:
        print("Live Gemini FAIL:", type(error).__name__)
        print(failure_hint(error))
        print("The keyword fallback was not used to hide this failure.")
        return False
    finally:
        logging.disable(previous_level)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true",
                        help="Use a privately configured replacement key to test the AI path")
    args = parser.parse_args(argv)
    if not check_connection():
        return 1
    if not args.live:
        return 0
    key = load_local_key()
    if not key:
        print("Live test PENDING: add a replacement GEMINI_API_KEY privately.")
        print("Use the environment or .streamlit/secrets.toml; never paste it in chat.")
        return 2
    return 0 if check_live(key) else 1


if __name__ == "__main__":
    raise SystemExit(main())
