import contextlib
import importlib.util
import io
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("gemini_check", Path(__file__).resolve().parents[1] / "scripts/check_gemini.py")
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class TestGeminiCheck(unittest.TestCase):
    def test_network_mode_never_loads_a_key(self):
        with patch.object(checker, "check_connection", return_value=True), patch.object(checker, "load_local_key") as load:
            self.assertEqual(checker.main([]), 0)
            load.assert_not_called()

    def test_live_without_key_is_pending(self):
        with patch.object(checker, "check_connection", return_value=True), patch.object(checker, "load_local_key", return_value=None), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(checker.main(["--live"]), 2)

    def test_live_uses_ai_directly_without_fallback(self):
        import extractor
        today = checker.datetime.now(checker.timezone(checker.timedelta(hours=5, minutes=30))).date()
        result = {"intent": "search", "origin": "Delhi", "destination": "Mumbai", "date": (today + checker.timedelta(days=1)).isoformat()}
        with patch.dict(os.environ), patch.object(extractor, "extract_with_ai", return_value=result), patch.object(extractor, "extract_with_keywords") as fallback, contextlib.redirect_stdout(io.StringIO()):
            self.assertTrue(checker.check_live("fake-test-key"))
            fallback.assert_not_called()

    def test_ai_failure_never_leaks_exception_or_key(self):
        import extractor
        output = io.StringIO()
        with patch.dict(os.environ), patch.object(extractor, "extract_with_ai", side_effect=RuntimeError("private-fake-key-in-error")), patch.object(extractor, "extract_with_keywords") as fallback, contextlib.redirect_stdout(output):
            self.assertFalse(checker.check_live("fake-test-key"))
            fallback.assert_not_called()
        self.assertNotIn("private-fake-key-in-error", output.getvalue())
        self.assertNotIn("fake-test-key", output.getvalue())

    def test_incorrect_ai_fields_fail(self):
        import extractor
        with patch.dict(os.environ), patch.object(extractor, "extract_with_ai", return_value={"origin": "Mumbai"}), contextlib.redirect_stdout(io.StringIO()):
            self.assertFalse(checker.check_live("fake-test-key"))

    def test_local_streamlit_secret_is_supported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".streamlit").mkdir()
            (root / ".streamlit/secrets.toml").write_text('GEMINI_API_KEY = "fake-local-key"')
            with patch.dict(os.environ, {}, clear=True), patch.object(checker, "ROOT", root):
                self.assertEqual(checker.load_local_key(), "fake-local-key")

    def test_status_hint_is_safe(self):
        self.assertIn("GEMINI_MODEL", checker.failure_hint(SimpleNamespace(code=404)))
        self.assertIn("Quota", checker.failure_hint(SimpleNamespace(code=429)))


if __name__ == "__main__":
    unittest.main()
