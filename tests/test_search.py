import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from search import search_flights

# Small fixed fixtures, deliberately separate from the changing dataset.
FLIGHTS = [
    {"id": "F1", "from": "Delhi", "to": "Mumbai", "date": "2026-10-12", "price": 5000, "duration": 130, "stops": 0},
    {"id": "F2", "from": "Delhi", "to": "Mumbai", "date": "2026-10-12", "price": 3500, "duration": 260, "stops": 1},
    {"id": "F3", "from": "Delhi", "to": "Mumbai", "date": "2026-10-12", "price": 4200, "duration": 95, "stops": 0},
    {"id": "F4", "from": "Delhi", "to": "Mumbai", "date": "2026-10-13", "price": 2000, "duration": 120, "stops": 0},
    {"id": "F5", "from": "Delhi", "to": "Goa", "date": "2026-10-12", "price": 3000, "duration": 150, "stops": 0},
    {"id": "F6", "from": "Pune", "to": "Mumbai", "date": "2026-10-12", "price": 1000, "duration": 60, "stops": 0},
]

TIES = [
    {"id": "B", "from": "A", "to": "Z", "date": "d", "price": 100, "duration": 50, "stops": 0},
    {"id": "A", "from": "A", "to": "Z", "date": "d", "price": 100, "duration": 50, "stops": 0},
    {"id": "C", "from": "A", "to": "Z", "date": "d", "price": 100, "duration": 50, "stops": 0},
]


def ids(result):
    return [f["id"] for f in result]


class TestSearchFlights(unittest.TestCase):
    def test_01_route_and_date_only_matches(self):
        r = search_flights(FLIGHTS, "Delhi", "Mumbai", "2026-10-12")
        self.assertEqual(set(ids(r)), {"F1", "F2", "F3"})

    def test_02_wrong_route_returns_empty(self):
        self.assertEqual(search_flights(FLIGHTS, "Goa", "Delhi", "2026-10-12"), [])

    def test_03_wrong_date_returns_empty(self):
        self.assertEqual(search_flights(FLIGHTS, "Delhi", "Mumbai", "2026-11-01"), [])

    def test_04_price_sort_cheapest_first(self):
        r = search_flights(FLIGHTS, "Delhi", "Mumbai", "2026-10-12", sort_by="price")
        self.assertEqual(ids(r), ["F2", "F3", "F1"])

    def test_05_duration_sort_shortest_first(self):
        r = search_flights(FLIGHTS, "Delhi", "Mumbai", "2026-10-12", sort_by="duration")
        self.assertEqual(ids(r), ["F3", "F1", "F2"])

    def test_06_price_at_limit_included(self):
        r = search_flights(FLIGHTS, "Delhi", "Mumbai", "2026-10-12", max_price=4200)
        self.assertIn("F3", ids(r))

    def test_07_above_limit_excluded(self):
        r = search_flights(FLIGHTS, "Delhi", "Mumbai", "2026-10-12", max_price=4199)
        self.assertNotIn("F3", ids(r))
        self.assertNotIn("F1", ids(r))
        self.assertEqual(ids(r), ["F2"])

    def test_08_non_stop_only_zero_stops(self):
        r = search_flights(FLIGHTS, "Delhi", "Mumbai", "2026-10-12", non_stop=True)
        self.assertTrue(all(f["stops"] == 0 for f in r))
        self.assertEqual(set(ids(r)), {"F1", "F3"})

    def test_09_combined_filters(self):
        r = search_flights(FLIGHTS, "Delhi", "Mumbai", "2026-10-12",
                           max_price=4500, non_stop=True, sort_by="duration")
        self.assertEqual(ids(r), ["F3"])

    def test_10_ties_stable_by_id_and_input_unchanged(self):
        before = copy.deepcopy(TIES)
        r = search_flights(TIES, "A", "Z", "d")
        self.assertEqual(ids(r), ["A", "B", "C"])
        self.assertEqual(TIES, before)
        self.assertIsNot(r, TIES)
        r[0]["price"] = 999
        self.assertEqual(TIES, before)


class TestInvalidArguments(unittest.TestCase):
    def test_invalid_arguments_raise_value_error(self):
        bad_calls = [
            dict(flights=None, origin="Delhi", destination="Mumbai", date="x"),
            dict(flights=[], origin="", destination="Mumbai", date="x"),
            dict(flights=[], origin="Delhi", destination="Mumbai", date="x", max_price="100"),
            dict(flights=[], origin="Delhi", destination="Mumbai", date="x", max_price=-1),
            dict(flights=[], origin="Delhi", destination="Mumbai", date="x", non_stop="yes"),
            dict(flights=[], origin="Delhi", destination="Mumbai", date="x", sort_by="airline"),
        ]
        for kwargs in bad_calls:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    search_flights(**kwargs)


if __name__ == "__main__":
    unittest.main()
