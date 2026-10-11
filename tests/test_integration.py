import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch
from integration import find_matches, load_flights, prepare_request
import extractor

TODAY = date(2026, 10, 11)
STATE = {"intent": "search", "origin": "Delhi", "destination": "Mumbai", "date": "2026-10-12"}
FLIGHTS = [
    {"id":"F1","airline":"Demo Air","from":"Delhi","to":"Mumbai","date":"2026-10-12","departure":"10:00","arrival":"12:00","duration":120,"stops":0,"price":5000},
    {"id":"F2","airline":"Demo Air","from":"Delhi","to":"Mumbai","date":"2026-10-12","departure":"12:00","arrival":"16:00","duration":240,"stops":1,"price":3000},
]


class TestIntegration(unittest.TestCase):
    def prepare(self, raw, state=None):
        return prepare_request("test", state or {}, TODAY, lambda *a: raw)

    def test_missing_destination_is_requested(self):
        state, status, _ = self.prepare({"intent":"search_flights","origin":"Delhi"})
        self.assertEqual((status, state["asking"]), ("clarify", "destination"))

    def test_date_reply_preserves_route_with_original_fallback(self):
        context = {"intent":"search","origin":"Delhi","destination":"Mumbai","asking":"date"}
        with patch.object(extractor, "extract_with_ai", side_effect=RuntimeError("offline test")):
            state, status, _ = prepare_request("tomorrow", context, TODAY, extractor.extract_request)
        self.assertEqual(status, "ready")
        self.assertEqual((state["origin"],state["destination"],state["date"]), ("Delhi","Mumbai","2026-10-12"))

    def test_city_reply_preserves_other_details(self):
        context = {"intent":"search","origin":"Delhi","date":"2026-10-12","asking":"destination"}
        with patch.object(extractor, "extract_with_ai", side_effect=RuntimeError("offline test")):
            state, status, _ = prepare_request("Mumbai", context, TODAY, extractor.extract_request)
        self.assertEqual(status,"ready")
        self.assertEqual(state["destination"],"Mumbai")

    def test_past_date_prompts_again(self):
        state, status, _ = self.prepare({**STATE,"date":"2026-10-05"})
        self.assertEqual((status,state["asking"],state["date"]),("clarify","date",None))

    def test_unsupported_city_prompts_again(self):
        state, status, _ = self.prepare({**STATE,"destination":"Goa"})
        self.assertEqual((status,state["destination"]),("clarify",None))

    def test_departure_sort_cannot_reach_search(self):
        _,status,_ = self.prepare({**STATE,"sort_by":"departure"})
        self.assertEqual(status,"clarify")

    def test_context_is_not_mutated(self):
        original = dict(STATE)
        prepare_request("help", original, TODAY, lambda *a: {"intent":"help"})
        self.assertEqual(original,STATE)

    def test_invalid_budgets_are_rejected(self):
        for price in (True, "5000", -1, float("nan"), float("inf")):
            with self.subTest(price=price):
                _,status,_ = self.prepare({**STATE,"max_price":price})
                self.assertEqual(status,"clarify")

    def test_defaults_and_explicit_false(self):
        state = {**STATE,"sort_by":None,"non_stop":None}
        self.assertEqual([f["id"] for f in find_matches(FLIGHTS,state)],["F2","F1"])
        self.assertEqual([f["id"] for f in find_matches(FLIGHTS,{**state,"non_stop":True},stops_override=False)],["F2","F1"])

    def test_sidebar_overrides_chat(self):
        state = {**STATE,"sort_by":"price","max_price":4000,"non_stop":False}
        self.assertEqual([f["id"] for f in find_matches(FLIGHTS,state,"duration",6000,True)],["F1"])

    def test_loading_distinguishes_missing_and_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"flights.json"
            self.assertIsNone(load_flights(path))
            path.write_text("[]")
            self.assertEqual(load_flights(path),[])

    def test_loading_rejects_invalid_records(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/"flights.json"
            for records in ({"flights":FLIGHTS}, [{**FLIGHTS[0],"departure":"28:00"}], [FLIGHTS[0],FLIGHTS[0]], [{**FLIGHTS[0],"price":-5}]):
                with self.subTest(records=records):
                    path.write_text(json.dumps(records))
                    with self.assertRaises(ValueError):
                        load_flights(path)
            path.write_text(json.dumps(FLIGHTS))
            self.assertEqual(load_flights(path),FLIGHTS)
