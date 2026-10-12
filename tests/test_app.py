import json
import time
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
        app.session_state['account_user']={'id':'test-user','name':'Demo','email':'demo@example.com','expires':time.time()+900}
        app.run()
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
        app.selectbox(key="stops_choice").select("Nonstop only").run()
        self.assertEqual(len(app.exception),0)
        cards = [m.value for m in app.markdown if '<div class="flight-card">' in m.value]
        self.assertEqual(len(cards), 1)
        self.assertIn("Demo Air · F1", cards[0])
        self.assertNotIn("Demo Air · F2", cards[0])
        app.button(key="clear_chat").click().run()
        self.assertEqual(app.session_state["request"],{})
        self.assertIsNone(app.session_state["results"])
        self.assertEqual(len(app.session_state["messages"]),1)

    def test_invalid_flight_data_reports_setup_error(self):
        (self.root / "flights.json").write_text('{"not":"a list"}')
        app = self.app()
        self.assertTrue(app.error)

    def test_sidebar_budget_and_sort_override_chat_and_clear_resets_filters(self):
        today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
        base = {"airline":"Demo Air","from":"Delhi","to":"Mumbai","date":today,
                "departure":"10:00","arrival":"12:00","duration":120,"stops":0}
        records = [{**base,"id":"FAST","price":5000},
                   {**base,"id":"CHEAP","price":3000,"duration":240,"stops":1}]
        (self.root / "flights.json").write_text(json.dumps(records))
        app = self.app()
        app.chat_input[0].set_value("cheapest Delhi to Mumbai today under 6000").run()
        app.selectbox(key="sort_choice").select("Shortest duration").run()
        cards = [m.value for m in app.markdown if '<div class="flight-card">' in m.value]
        self.assertIn("FAST", cards[0])
        app.checkbox[0].check().run()
        app.number_input[0].set_value(3500).run()
        cards = [m.value for m in app.markdown if '<div class="flight-card">' in m.value]
        self.assertEqual(len(cards), 1)
        self.assertIn("CHEAP", cards[0])
        app.button(key="clear_chat").click().run()
        self.assertEqual(app.selectbox(key="sort_choice").value, "Use chat preference")
        self.assertEqual(app.selectbox(key="stops_choice").value, "Use chat preference")
        self.assertFalse(app.checkbox[0].value)
        self.assertEqual(app.session_state["request"], {})

    def test_dataset_text_is_escaped_inside_frontend_cards(self):
        today = datetime.now(ZoneInfo("Asia/Kolkata")).date().isoformat()
        records = [{"id":"SAFE","airline":"<script>unsafe()</script>",
                    "from":"Delhi","to":"Mumbai","date":today,
                    "departure":"10:00","arrival":"12:00","duration":120,"stops":0,"price":5000}]
        (self.root / "flights.json").write_text(json.dumps(records))
        app = self.app()
        app.chat_input[0].set_value("Delhi to Mumbai today").run()
        cards = [m.value for m in app.markdown if '<div class="flight-card">' in m.value]
        self.assertEqual(len(cards), 1)
        self.assertIn("&lt;script&gt;", cards[0])
        self.assertNotIn("<script>", cards[0])

