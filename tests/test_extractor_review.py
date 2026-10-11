import json
import unittest
from datetime import date
from unittest.mock import patch
import extractor

TODAY = date(2026, 10, 11)


class TestExtractorReview(unittest.TestCase):
    def offline(self, message, context=None):
        with patch.object(extractor, "extract_with_ai", side_effect=TimeoutError("offline")):
            return extractor.extract_request(message, TODAY, context)

    def test_public_fallback_preserves_rejected_date_reason(self):
        result = extractor.extract_with_keywords("Delhi to Mumbai yesterday", TODAY)
        self.assertEqual(result.problems, {"date": "past"})

    def test_unsupported_sort_has_a_clarification_signal(self):
        result = self.offline("earliest Delhi to Mumbai tomorrow")
        self.assertEqual(result.problems, {"sort_by": "unsupported"})

    def test_sort_choice_can_answer_the_clarification(self):
        for value in ("price", "duration"):
            with self.subTest(value=value):
                result = self.offline(value, {"intent": "search", "asking": "sort_by"})
                self.assertEqual((result["intent"], result["sort_by"]), ("search", value))

    def test_nonfinite_ai_budget_triggers_keyword_recovery(self):
        for value in (float("nan"), float("inf")):
            raw = {k: None for k in extractor.FIELDS}
            raw.update(intent="search", max_price=value)
            with patch.object(extractor, "_ask_gemini", return_value=json.dumps(raw)):
                result, source = extractor._extract("Delhi to Mumbai tomorrow", TODAY)
            self.assertEqual(source, "keywords")
            self.assertIsNone(result["max_price"])

    def test_clear_date_corrects_future_ai_miscalculation(self):
        raw = {k: None for k in extractor.FIELDS}
        raw.update(intent="search", date="2030-10-12")
        with patch.object(extractor, "_ask_gemini", return_value=json.dumps(raw)):
            result, source = extractor._extract("Delhi to Mumbai tomorrow", TODAY)
        self.assertEqual((source, result["date"]), ("ai", "2026-10-12"))

    def test_exception_details_cannot_leak_a_credential(self):
        with patch.object(extractor, "extract_with_ai", side_effect=RuntimeError("fake-secret-credential")):
            with self.assertLogs("extractor", level="WARNING") as logs:
                result, _ = extractor._extract("Delhi to Mumbai tomorrow", TODAY)
        self.assertNotIn("fake-secret-credential", result.ai_error)
        self.assertNotIn("fake-secret-credential", " ".join(logs.output))

    def test_live_check_uses_current_day_instead_of_offline_fixture(self):
        import contextlib
        import io
        import test_extractor as submitted

        live_day = date(2040, 1, 1)
        answer = extractor.ExtractResult({
            "intent": "cheapest", "origin": "Bengaluru", "destination": "Kolkata",
            "date": "2040-01-02", "sort_by": "price", "max_price": None, "non_stop": True
        }, source="ai")
        outcome = unittest.TestResult()
        with patch.object(submitted.TestLiveGemini, "__unittest_skip__", False), \
             patch.object(submitted, "LIVE_KEY", "fake-private-test-key"), \
             patch.object(extractor, "_as_date", return_value=live_day) as current_day, \
             patch.object(submitted, "_extract", return_value=(answer, "ai")) as extract, \
             contextlib.redirect_stdout(io.StringIO()):
            submitted.TestLiveGemini("test_real_gemini_answers").run(outcome)
        self.assertEqual(outcome.testsRun, 1)
        self.assertEqual((outcome.errors, outcome.failures, outcome.skipped), ([], [], []))
        current_day.assert_called_once_with(None)
        extract.assert_called_once_with(
            "cheapest nonstop flight from Bangalore to Calcutta tomorrow", live_day
        )
