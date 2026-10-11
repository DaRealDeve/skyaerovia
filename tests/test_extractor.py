"""
Tests for extractor.py.

Run from the project folder:
    python -m unittest discover -s tests -v

All tests are offline (no API key, no internet): Gemini is replaced by a mock.
The very last test talks to the REAL Gemini. It is skipped unless GEMINI_API_KEY is set
in your environment, or saved in .streamlit/secrets.toml (never put the key in this file).
"""

import json
import os
import re
import sys
import unittest
from datetime import date, datetime
from unittest import mock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import extractor  # noqa: E402
import logging  # noqa: E402

logging.getLogger("extractor").setLevel(logging.ERROR)  # keep test output clean
from extractor import _extract, extract_request  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_live_key():
    """The key for the live test: the GEMINI_API_KEY environment variable, or else the
    private file .streamlit/secrets.toml (which .gitignore keeps out of GitHub).
    The key is never printed."""
    key = os.environ.get("GEMINI_API_KEY")
    if key:
        return key
    secrets = os.path.join(ROOT, ".streamlit", "secrets.toml")
    if os.path.exists(secrets):
        with open(secrets, encoding="utf-8") as f:
            m = re.search(r'^\s*GEMINI_API_KEY\s*=\s*["\']([^"\']+)["\']', f.read(), re.MULTILINE)
        if m:
            return m.group(1)
    return None


LIVE_KEY = _load_live_key()  # read BEFORE the tests clear the environment variable

T = date(2026, 10, 11)  # fixed "today" (a Sunday) so results never change
TOMORROW = "2026-10-12"
SEVEN_KEYS = {"intent", "origin", "destination", "date", "sort_by", "max_price", "non_stop"}

SEARCH_CTX = {"intent": "search", "origin": "Delhi", "destination": "Mumbai"}


def expected(**fields):
    """The seven keys, everything None unless given."""
    base = {key: None for key in SEVEN_KEYS}
    base.update(fields)
    return base


class OfflineTestCase(unittest.TestCase):
    """Base class: no API key in the environment, so the keyword fallback answers."""

    def setUp(self):
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("GEMINI_API_KEY", None)

    def run_kw(self, message, context=None, today=T):
        result, source = _extract(message, today, context)
        self.assertEqual(source, "keywords")
        return result


# ==========================================================================
# The ten checks requested in review
# ==========================================================================
class TestRequestedChecks(OfflineTestCase):
    def test_complete_flight_search(self):
        r = self.run_kw("Show me flights from Delhi to Mumbai on 2026-10-15 under 6000 non-stop")
        self.assertEqual(r, expected(intent="search", origin="Delhi", destination="Mumbai",
                                     date="2026-10-15", max_price=6000, non_stop=True))
        self.assertEqual(r.problems, {})

    def test_tomorrow_uses_the_supplied_date(self):
        self.assertEqual(self.run_kw("flights from Delhi to Goa tomorrow")["date"], TOMORROW)
        # a different supplied date gives a different answer (year rollover too)
        r = self.run_kw("flights from Delhi to Goa tomorrow", today=date(2026, 12, 31))
        self.assertEqual(r["date"], "2027-01-01")
        # "today" may be a string or a datetime
        self.assertEqual(self.run_kw("Delhi to Goa tomorrow", today="2026-03-01")["date"], "2026-03-02")
        self.assertEqual(self.run_kw("Delhi to Goa tomorrow", today=datetime(2026, 3, 1, 23, 59))["date"],
                         "2026-03-02")
        self.assertEqual(self.run_kw("flights Delhi to Goa day after tomorrow")["date"], "2026-10-13")

    def test_city_aliases(self):
        cases = [
            ("flights from Bangalore to Calcutta tomorrow", "Bengaluru", "Kolkata"),
            ("flights from Bombay to new delhi tomorrow", "Mumbai", "Delhi"),
            ("BOM to DEL tomorrow", "Mumbai", "Delhi"),
            ("flights from madras to hyd tomorrow", "Chennai", "Hyderabad"),
            ("flights from Poona to Amdavad", "Pune", "Ahmedabad"),
        ]
        for message, origin, destination in cases:
            with self.subTest(message):
                r = self.run_kw(message)
                self.assertEqual((r["origin"], r["destination"]), (origin, destination))

    def test_budget_and_nonstop(self):
        budgets = [
            ("flights Delhi to Mumbai under ₹5,000", 5000),
            ("flights Delhi to Mumbai below 5k", 5000),
            ("flights Delhi to Mumbai within Rs 7500", 7500),
            ("flights Delhi to Mumbai under 1 lakh", 100000),
            ("flights Delhi to Mumbai 5000 se kam", 5000),
            ("flights Delhi to Mumbai under 2 hours", None),  # hours are not a budget
            ("flights Delhi to Mumbai", None),
        ]
        for message, price in budgets:
            with self.subTest(message):
                self.assertEqual(self.run_kw(message)["max_price"], price)

        nonstop = [
            ("non-stop flights Delhi to Mumbai", True),
            ("nonstop flights Delhi to Mumbai", True),
            ("direct flights Delhi to Mumbai", True),
            ("flights Delhi to Mumbai without stops", True),
            ("flights Delhi to Mumbai", None),
        ]
        for message, value in nonstop:
            with self.subTest(message):
                self.assertIs(self.run_kw(message)["non_stop"], value)

    def test_missing_city(self):
        r = self.run_kw("flights to Goa tomorrow")
        self.assertEqual((r["intent"], r["origin"], r["destination"]), ("search", None, "Goa"))
        r = self.run_kw("flights from Delhi")
        self.assertEqual((r["intent"], r["origin"], r["destination"]), ("search", "Delhi", None))
        r = self.run_kw("show me flights")
        self.assertEqual((r["intent"], r["origin"], r["destination"]), ("search", None, None))

    def test_city_only_followup(self):
        # Skye asked "Where to?" and the user answers with just a city
        r = self.run_kw("Mumbai", {"intent": "search", "origin": "Delhi", "asking": "destination"})
        self.assertEqual(r, expected(intent="search", destination="Mumbai"))  # origin is NOT copied back

        r = self.run_kw("Delhi", {"intent": "search", "destination": "Mumbai", "asking": "origin"})
        self.assertEqual(r, expected(intent="search", origin="Delhi"))

        r = self.run_kw("to Goa", {"intent": "search", "origin": "Delhi", "asking": "destination"})
        self.assertEqual(r, expected(intent="search", destination="Goa"))

        # the app keeps the details but sends no "asking": the first missing one is the answer
        r = self.run_kw("Bangalore", {"intent": "search", "origin": "Delhi"})
        self.assertEqual(r, expected(intent="search", destination="Bengaluru"))

        # the question text works too
        r = self.run_kw("Pune", {"last_question": "Where are you flying from?"})
        self.assertEqual(r, expected(intent="search", origin="Pune"))

        # a city is only accepted when we really asked for one
        self.assertEqual(self.run_kw("Mumbai")["intent"], "unknown")
        self.assertEqual(self.run_kw("hello", {"intent": "search", "asking": "destination"})["destination"], None)

    def test_date_only_followup(self):
        # Skye asked "Which date?" and the user says "tomorrow"
        ctx = dict(SEARCH_CTX, asking="date")
        r = self.run_kw("tomorrow", ctx)
        self.assertEqual(r, expected(intent="search", date=TOMORROW))  # not "other" / "unknown"

        self.assertEqual(self.run_kw("15 oct", ctx)["date"], "2026-10-15")
        self.assertEqual(self.run_kw("next friday", ctx)["date"], "2026-10-16")

        # no "asking": the date is the first missing detail
        self.assertEqual(self.run_kw("tomorrow", SEARCH_CTX)["date"], TOMORROW)
        # the question text works too
        r = self.run_kw("tomorrow", {"last_question": "Which date?"})
        self.assertEqual((r["intent"], r["date"]), ("search", TOMORROW))
        # a "cheapest" search stays a "cheapest" search
        r = self.run_kw("tomorrow", {"intent": "cheapest", "asking": "date"})
        self.assertEqual((r["intent"], r["date"]), ("cheapest", TOMORROW))
        # with no context at all, a bare "tomorrow" is not a flight request
        self.assertEqual(self.run_kw("tomorrow")["intent"], "unknown")

    def test_past_and_invalid_dates(self):
        cases = [
            ("flights from Delhi to Goa on 2026-10-05", "past"),
            ("flights from Delhi to Goa yesterday", "past"),
            ("flights from Delhi to Goa on 12 jan 2025", "past"),
            ("flights from Delhi to Goa on 5 oct", "past"),          # this year, already gone
            ("flights from Delhi to Goa on 2026-02-30", "invalid"),
            ("flights from Delhi to Goa on 31 sep", "invalid"),
            ("flights from Delhi to Goa on 32/10", "invalid"),
            ("flights from Delhi to Goa on 2026-13-45", "invalid"),
        ]
        for message, problem in cases:
            with self.subTest(message):
                r = self.run_kw(message)
                self.assertIsNone(r["date"])                  # rejected...
                self.assertEqual(r.problems, {"date": problem})  # ...with the reason
                self.assertEqual((r["origin"], r["destination"]), ("Delhi", "Goa"))  # rest is kept

        # today itself is fine
        r = self.run_kw("flights from Delhi to Goa today")
        self.assertEqual((r["date"], r.problems), ("2026-10-11", {}))
        # a date reply that is in the past is rejected too
        r = self.run_kw("yesterday", dict(SEARCH_CTX, asking="date"))
        self.assertEqual((r["intent"], r["date"], r.problems), ("search", None, {"date": "past"}))

    def test_cheapest_and_fastest(self):
        r = self.run_kw("cheapest flight from Delhi to Mumbai")
        self.assertEqual((r["intent"], r["sort_by"]), ("cheapest", "price"))
        r = self.run_kw("show me the fastest flights Delhi to Mumbai")
        self.assertEqual((r["intent"], r["sort_by"]), ("search", "duration"))
        r = self.run_kw("fastest one", SEARCH_CTX)
        self.assertEqual((r["intent"], r["sort_by"]), ("search", "duration"))
        r = self.run_kw("sort by price", SEARCH_CTX)
        self.assertEqual((r["intent"], r["sort_by"]), ("search", "price"))
        self.assertEqual(self.run_kw("cheapest")["intent"], "cheapest")

    def test_earliest_is_not_sent_to_search(self):
        # the search module cannot sort by departure: explain the choices instead
        r = self.run_kw("earliest flight from Delhi to Mumbai tomorrow")
        self.assertEqual((r["intent"], r["sort_by"]), ("help", None))
        self.assertEqual((r["origin"], r["destination"], r["date"]), ("Delhi", "Mumbai", TOMORROW))

    def test_gemini_failure_triggers_the_fallback(self):
        message = "cheapest nonstop flights from Bangalore to Calcutta tomorrow"
        errors = [TimeoutError("timed out"), ConnectionError("no network"),
                  RuntimeError("429 quota exceeded"), ValueError("anything")]
        for error in errors:
            with self.subTest(type(error).__name__):
                with mock.patch.object(extractor, "_ask_gemini", side_effect=error):
                    r, source = _extract(message, T)
                self.assertEqual(source, "keywords")
                self.assertIn(type(error).__name__, r.ai_error)
                self.assertEqual((r["intent"], r["origin"], r["destination"], r["date"],
                                  r["sort_by"], r["non_stop"]),
                                 ("cheapest", "Bengaluru", "Kolkata", TOMORROW, "price", True))

    def test_no_api_key_uses_the_fallback(self):
        r, source = _extract("flights from Delhi to Goa tomorrow", T)
        self.assertEqual(source, "keywords")
        self.assertIn("GEMINI_API_KEY", r.ai_error)
        self.assertEqual(r["destination"], "Goa")


# ==========================================================================
# The seven failures from the 50-case chat round
# ==========================================================================
class TestFiftyCaseFailures(OfflineTestCase):
    def test_T24_negative_budget_is_flagged_not_ignored(self):
        r = self.run_kw("Delhi to Mumbai tomorrow under -100")
        self.assertEqual((r["origin"], r["destination"], r["date"]), ("Delhi", "Mumbai", TOMORROW))
        self.assertEqual(r["max_price"], -100)                 # the bad number is kept as the signal
        self.assertEqual(r.problems, {"max_price": "invalid"})  # the app asks for a valid budget
        self.assertEqual(self.run_kw("Delhi to Mumbai under 0").problems, {"max_price": "invalid"})
        self.assertEqual(self.run_kw("Delhi to Mumbai under 5000").problems, {})

    def test_T31_stops_allowed_clears_nonstop(self):
        ctx = dict(SEARCH_CTX, non_stop=True)
        r = self.run_kw("Delhi to Mumbai tomorrow, stops are fine", ctx)
        self.assertIs(r["non_stop"], False)                    # False, not None
        self.assertEqual((r["origin"], r["destination"], r["date"]), ("Delhi", "Mumbai", TOMORROW))
        for phrase in ("stops are fine", "layovers are ok", "connecting flights are fine", "i don't mind stops"):
            with self.subTest(phrase):
                self.assertIs(self.run_kw(f"Delhi to Mumbai {phrase}")["non_stop"], False)

    def test_T40_budget_only_reply(self):
        ctx = dict(SEARCH_CTX, date=TOMORROW, asking="max_price")
        self.assertEqual(self.run_kw("5000", ctx), expected(intent="search", max_price=5000))
        self.assertEqual(self.run_kw("₹5,000", ctx)["max_price"], 5000)
        self.assertEqual(self.run_kw("5k", ctx)["max_price"], 5000)
        # a bare number is NOT a budget unless we asked for one
        self.assertIsNone(self.run_kw("5000")["max_price"])
        self.assertIsNone(self.run_kw("5000", dict(SEARCH_CTX, date=TOMORROW))["max_price"])
        # a bad budget reply is flagged
        r = self.run_kw("-100", ctx)
        self.assertEqual((r["max_price"], r.problems), (-100, {"max_price": "invalid"}))

    def test_T41_hinglish_tomorrow(self):
        r = self.run_kw("Delhi se Mumbai kal")
        self.assertEqual(r, expected(intent="search", origin="Delhi", destination="Mumbai", date=TOMORROW))
        # "kal" with a past-tense word could mean yesterday: ask, don't guess
        r = self.run_kw("Delhi se Mumbai kal gaya tha")
        self.assertEqual((r["date"], r.problems), (None, {"date": "ambiguous"}))

    def test_T42_hinglish_today(self):
        r = self.run_kw("Delhi to Mumbai aaj")
        self.assertEqual(r, expected(intent="search", origin="Delhi", destination="Mumbai", date="2026-10-11"))

    def test_T45_hinglish_stops_allowed(self):
        ctx = dict(SEARCH_CTX, date=TOMORROW, non_stop=True)
        r = self.run_kw("layover chalega", ctx)
        self.assertEqual(r, expected(intent="search", non_stop=False))  # continues the saved search

    def test_T47_misspelled_tomorrow(self):
        r = self.run_kw("Delhi to Mumbai tomorow")
        self.assertEqual(r, expected(intent="search", origin="Delhi", destination="Mumbai", date=TOMORROW))
        self.assertEqual(self.run_kw("Delhi to Mumbai tommorow")["destination"], "Mumbai")


# ==========================================================================
# Output format: the same seven keys and agreed names every time
# ==========================================================================
class TestOutputFormat(OfflineTestCase):
    MESSAGES = [
        "", "   ", "hello", "what can you do", "cancel my booking", "is my flight delayed?",
        "book a hotel in goa", "cheapest flight Delhi to Mumbai tomorrow under 5000 non-stop",
        "earliest flight Delhi to Mumbai", "flights to Goa on 2026-02-30", "fastest",
    ]

    def test_seven_keys_and_agreed_values(self):
        for message in self.MESSAGES:
            with self.subTest(message):
                r = self.run_kw(message)
                self.assertIsInstance(r, dict)
                self.assertEqual(set(r), SEVEN_KEYS)
                self.assertIn(r["intent"], ("search", "cheapest", "help", "unknown"))
                self.assertIn(r["sort_by"], (None, "price", "duration"))
                self.assertIn(r["non_stop"], (None, True, False))
                json.dumps(r)  # a plain dict: JSON-safe

    def test_help_and_unknown(self):
        for message in ("hello", "hi", "what can you do", "help"):
            self.assertEqual(self.run_kw(message)["intent"], "help", message)
        for message in ("cancel my booking", "is my flight delayed?", "book a hotel in goa", "", "thanks"):
            self.assertEqual(self.run_kw(message)["intent"], "unknown", message)


# ==========================================================================
# The Gemini path (Gemini is mocked: no key, no internet)
# ==========================================================================
def fake_gemini(payload):
    text = payload if isinstance(payload, str) else json.dumps(payload)
    return mock.patch.object(extractor, "_ask_gemini", return_value=text)


def ai_answer(**fields):
    base = {key: None for key in SEVEN_KEYS}
    base["intent"] = "search"
    base.update(fields)
    return base


class TestGeminiPath(OfflineTestCase):
    def test_valid_answer_is_used_and_normalised(self):
        answer = ai_answer(origin="Bangalore", destination="BOM", date=TOMORROW, sort_by="price",
                           max_price="5,000", non_stop=True)
        with fake_gemini(answer):
            r, source = _extract("cheapest flight bangalore to bom tomorrow under 5000 non-stop", T)
        self.assertEqual(source, "ai")
        self.assertIsNone(r.ai_error)
        self.assertEqual(r, expected(intent="search", origin="Bengaluru", destination="Mumbai",
                                     date=TOMORROW, sort_by="price", max_price=5000, non_stop=True))

    def test_json_in_code_fences_is_accepted(self):
        text = "```json\n" + json.dumps(ai_answer(destination="Goa")) + "\n```"
        with fake_gemini(text):
            r, source = _extract("flights to Goa", T)
        self.assertEqual((source, r["destination"]), ("ai", "Goa"))

    def test_cheapest_intent_always_sorts_by_price(self):
        with fake_gemini(ai_answer(intent="cheapest", origin="Delhi", destination="Goa")):
            r, _ = _extract("cheapest Delhi to Goa", T)
        self.assertEqual((r["intent"], r["sort_by"]), ("cheapest", "price"))

    def test_malformed_or_invalid_ai_output_triggers_fallback(self):
        bad_outputs = {
            "not json": "Sorry, I can't help with that",
            "json list": ["a", "b"],
            "old intent name": ai_answer(intent="search_flights"),
            "other intent": ai_answer(intent="other"),
            "unsupported sort_by": ai_answer(sort_by="departure"),
            "bad date text": ai_answer(date="tomorrow"),
            "impossible date": ai_answer(date="2026-02-30"),
            "negative price": ai_answer(max_price=-5),
            "price not a number": ai_answer(max_price="cheap"),
            "bad non_stop": ai_answer(non_stop="maybe"),
        }
        for label, payload in bad_outputs.items():
            with self.subTest(label):
                with fake_gemini(payload):
                    r, source = _extract("flights from Delhi to Goa tomorrow", T)
                self.assertEqual(source, "keywords")
                self.assertTrue(r.ai_error)
                self.assertEqual((r["origin"], r["destination"], r["date"]), ("Delhi", "Goa", TOMORROW))

    def test_past_date_is_rejected_on_the_ai_path_too(self):
        # the user asked for a past date; the AI "helpfully" moved it to next year
        with fake_gemini(ai_answer(origin="Delhi", destination="Goa", date="2027-10-05")):
            r, source = _extract("flights from Delhi to Goa on 5 oct", T)
        self.assertEqual(source, "ai")
        self.assertIsNone(r["date"])
        self.assertEqual(r.problems, {"date": "past"})
        # the AI returned the past date as written
        with fake_gemini(ai_answer(origin="Delhi", destination="Goa", date="2026-10-05")):
            r, _ = _extract("flights from Delhi to Goa on 2026-10-05", T)
        self.assertEqual((r["date"], r.problems), (None, {"date": "past"}))
        # impossible date, and a rejected date the AI left empty
        with fake_gemini(ai_answer(origin="Delhi", destination="Goa", date=None)):
            r, _ = _extract("flights from Delhi to Goa on 31 sep", T)
        self.assertEqual((r["date"], r.problems), (None, {"date": "invalid"}))

    def test_ai_miscalculated_tomorrow_is_corrected_from_the_message(self):
        with fake_gemini(ai_answer(origin="Delhi", destination="Goa", date="2025-10-12")):
            r, source = _extract("flights from Delhi to Goa tomorrow", T)
        self.assertEqual((source, r["date"], r.problems), ("ai", TOMORROW, {}))
        # no clear date in the message: reject instead of guessing
        with fake_gemini(ai_answer(destination="Goa", date="2025-10-12")):
            r, _ = _extract("flights to Goa soon", T)
        self.assertEqual((r["date"], r.problems), (None, {"date": "past"}))

    def test_negative_budget_is_flagged_on_the_ai_path_too(self):
        with fake_gemini(ai_answer(origin="Delhi", destination="Mumbai", date=TOMORROW, max_price=None)):
            r, source = _extract("Delhi to Mumbai tomorrow under -100", T)
        self.assertEqual((source, r["max_price"], r.problems), ("ai", -100, {"max_price": "invalid"}))

    def test_earliest_becomes_help_on_the_ai_path(self):
        with fake_gemini(ai_answer(origin="Delhi", destination="Mumbai")):
            r, _ = _extract("earliest flight Delhi to Mumbai", T)
        self.assertEqual((r["intent"], r["sort_by"]), ("help", None))

    def test_context_is_sent_to_gemini(self):
        with fake_gemini(ai_answer(date=TOMORROW)) as ask:
            _extract("tomorrow", T, dict(SEARCH_CTX, asking="date"))
        sent_context = ask.call_args.args[2]
        self.assertEqual(sent_context["asking"], "date")

    def test_prompt_contains_todays_date_and_agreed_names(self):
        prompt = extractor.build_prompt(T)
        for text in ("2026-10-11", "Sunday", '"search"', '"cheapest"', '"help"', '"unknown"',
                     '"price" | "duration"'):
            self.assertIn(text, prompt)


# ==========================================================================
# LIVE test of the real Gemini connection (skipped without a key)
# ==========================================================================
@unittest.skipUnless(LIVE_KEY, "no key found: set GEMINI_API_KEY or create .streamlit/secrets.toml")
class TestLiveGemini(unittest.TestCase):
    def test_real_gemini_answers(self):
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": LIVE_KEY}):
            result, source = _extract("cheapest nonstop flight from Bangalore to Calcutta tomorrow", T)
        reason = (result.ai_error or "").replace(LIVE_KEY, "[KEY HIDDEN]")  # never show the key
        print(f"\n  model={extractor.MODEL} source={source} result={dict(result)} problems={result.problems}")
        self.assertEqual(source, "ai", f"Gemini did not answer. Reason: {reason}")
        self.assertEqual(result["intent"], "cheapest")
        self.assertEqual((result["origin"], result["destination"]), ("Bengaluru", "Kolkata"))
        self.assertEqual(result["date"], TOMORROW)
        self.assertEqual(result["sort_by"], "price")
        self.assertIs(result["non_stop"], True)


if __name__ == "__main__":
    unittest.main()
