import json
import shutil
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import patch
from zoneinfo import ZoneInfo

import extractor
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


class TestApp(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        shutil.copy(ROOT / "app.py", self.root / "app.py")
        self.mock = patch.object(extractor, "extract_with_ai", side_effect=RuntimeError("offline UI test"))
        self.mock.start()

    def tearDown(self):
        self.mock.stop()
        self.tmp.cleanup()

    def app(self):
        app = AppTest.from_file(str(self.root / "app.py"), default_timeout=10).run()
        self.assertEqual(len(app.exception),0)
        return app

    def test_missing_data_and_multi_turn_request(self):
        app = self.app()
        self.assertTrue(app.warning)
        for text in ("from Delhi", "Mumbai", "tomorrow"):
            app.chat_input[0].set_value(text).run()
            self.assertEqual(len(app.exception),0)
        self.assertEqual(app.session_state["request"]["destination"],"Mumbai")
        self.assertIn("waiting for the demo data",app.session_state["messages"][-1]["content"])

    def test_flights_filters_and_reset(self):
        today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
        base = {"airline":"Demo Air","from":"Delhi","to":"Mumbai","date":today,"departure":"10:00","arrival":"12:00","duration":120,"stops":0}
        records = [{**base,"id":"F1","price":5000},{**base,"id":"F2","price":3000,"stops":1}]
        (self.root / "flights.json").write_text(json.dumps(records))
        app = self.app()
        app.chat_input[0].set_value("Delhi to Mumbai today").run()
        self.assertEqual(len(app.exception),0)
        self.assertIn("2 simulated",app.session_state["messages"][-1]["content"])
        app.selectbox[1].select("Nonstop only").run()
        self.assertEqual(len(app.exception),0)
        self.assertTrue(any("F1" in m.value for m in app.markdown))
        self.assertFalse(any("F2" in m.value for m in app.markdown))
        app.button[0].click().run()
        self.assertEqual(app.session_state["request"],{})
        self.assertIsNone(app.session_state["results"])
        self.assertEqual(len(app.session_state["messages"]),1)

    def test_invalid_flight_data_reports_setup_error(self):
        (self.root / "flights.json").write_text('{"not":"a list"}')
        app = self.app()
        self.assertTrue(app.error)
