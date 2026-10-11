import importlib.util
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path

import extractor
from integration import CITIES, find_matches, load_flights, prepare_request
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("generate_flights", ROOT / "scripts/generate_flights.py")
generator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(generator)


class TestFlightData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = load_flights(ROOT / "flights.json")
        cls.first_day = min(date.fromisoformat(f["date"]) for f in cls.records)

    def test_sixty_flights_cover_eight_cities_and_seven_consecutive_days(self):
        self.assertEqual(len(self.records), 60)
        self.assertEqual(len({f["id"] for f in self.records}), 60)
        self.assertEqual({f["from"] for f in self.records}, set(CITIES))
        self.assertEqual({f["to"] for f in self.records}, set(CITIES))
        self.assertEqual({f["date"] for f in self.records},
                         {(self.first_day + timedelta(days=i)).isoformat() for i in range(7)})

    def test_times_match_duration_and_all_values_have_the_agreed_units(self):
        fields = {"id", "airline", "from", "to", "date", "departure", "arrival", "duration", "stops", "price"}
        for flight in self.records:
            with self.subTest(id=flight["id"]):
                self.assertEqual(set(flight), fields)
                departure = datetime.strptime(flight["date"] + " " + flight["departure"], "%Y-%m-%d %H:%M")
                arrival = datetime.strptime(flight["date"] + " " + flight["arrival"], "%Y-%m-%d %H:%M")
                self.assertEqual((arrival - departure).total_seconds() // 60, flight["duration"])
                self.assertNotEqual(flight["from"], flight["to"])
                self.assertTrue(flight["airline"].strip())
                self.assertIn(flight["stops"], (0, 1))
                self.assertGreaterEqual(flight["duration"], 60)
                self.assertGreaterEqual(flight["price"], 2500)
                self.assertLessEqual(flight["price"], 15000)

    def test_chat_search_budget_nonstop_and_duration_use_the_actual_dataset(self):
        with patch.object(extractor, "extract_with_ai", side_effect=RuntimeError("offline dataset test")):
            state, status, _ = prepare_request("Delhi to Mumbai tomorrow", {}, self.first_day, extractor.extract_request)
        self.assertEqual(status, "ready")
        matches = find_matches(self.records, state)
        self.assertEqual(len(matches), 3)
        self.assertEqual([f["price"] for f in matches], sorted(f["price"] for f in matches))
        direct = find_matches(self.records, state, budget_override=5000, stops_override=True)
        self.assertEqual(len(direct), 2)
        self.assertTrue(all(f["stops"] == 0 and f["price"] <= 5000 for f in direct))
        fastest = find_matches(self.records, state, sort_override="duration")
        self.assertEqual([f["duration"] for f in fastest], sorted(f["duration"] for f in fastest))
        self.assertNotEqual(matches[0]["id"], fastest[0]["id"])
        self.assertEqual(find_matches(self.records, state, budget_override=2500), [])

    def test_refresh_handles_month_and_year_rollover_and_remains_loadable(self):
        for start in (date(2026, 12, 29), date(2028, 2, 27)):
            with self.subTest(start=start), tempfile.TemporaryDirectory() as tmp:
                records = generator.generate(start)
                path = Path(tmp) / "flights.json"
                path.write_text(json.dumps(records), encoding="utf-8")
                self.assertEqual(len(load_flights(path)), 60)
                self.assertEqual({f["date"] for f in records},
                                 {(start + timedelta(days=i)).isoformat() for i in range(7)})
