"""Run the 50 agreed sentences through the complete Streamlit UI offline.

The existing case fixture intentionally uses 2026-10-11 as today. Only the
temporary test copy's clock is fixed; the real app uses the current IST date.
No API key is used and the keyword fallback is forced for reproducible checks.
"""
import json
import logging
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import extractor
from integration import find_matches, load_flights
from streamlit.testing.v1 import AppTest


def run():
    cases = json.loads((ROOT / "tests/chat_cases.json").read_text())
    flights = load_flights(ROOT / "flights.json")
    source = (ROOT / "app.py").read_text()
    clock = 'today = datetime.now(ZoneInfo("Asia/Kolkata")).date()'
    if source.count(clock) != 1:
        raise RuntimeError("Cannot fix the test copy's clock")
    source = source.replace(clock, 'today = datetime(2026, 10, 11).date()')
    previous_logging = logging.root.manager.disable
    logging.disable(logging.CRITICAL)
    results = []
    try:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "app.py").write_text(source)
            shutil.copy(ROOT / "flights.json", root / "flights.json")
            if (ROOT / "assets/logo.jpg").exists():
                (root / "assets").mkdir()
                shutil.copy(ROOT / "assets/logo.jpg", root / "assets/logo.jpg")
            with patch.object(extractor, "extract_with_ai", side_effect=RuntimeError("offline UI acceptance")):
                for case in cases:
                    try:
                        app = AppTest.from_file(str(root / "app.py"), default_timeout=10).run()
                        app.session_state["request"] = dict(case.get("context", {}))
                        app.chat_input[0].set_value(case["message"]).run()
                        if app.exception:
                            raise RuntimeError("Streamlit reported an exception")
                        state = dict(app.session_state["request"])
                        ready = app.session_state["results"] is not None
                        status = "ready" if ready else "clarify" if state.get("asking") else "help"
                        actual = {"status": status, **state}
                        mismatches = {k:{"expected":v,"actual":actual.get(k)}
                                      for k,v in case["expected"].items() if actual.get(k) != v}
                        cards = [m.value for m in app.markdown if '<div class="flight-card">' in m.value]
                        expected_cards = len(find_matches(flights, state)) if ready else 0
                        if len(cards) != expected_cards:
                            mismatches["cards"] = {"expected":expected_cards,"actual":len(cards)}
                        results.append({**case,"actual":actual,"cards":len(cards),
                                        "passed":not mismatches,"mismatches":mismatches})
                    except Exception as error:
                        results.append({**case,"passed":False,"error":type(error).__name__})
    finally:
        logging.disable(previous_logging)
    passed = sum(r["passed"] for r in results)
    (ROOT / "docs/ui-chat-results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    report = ["# Full-interface conversation checks", "",
              f"Result: **{passed}/{len(results)} passed.**", "",
              "Scope: Richa's integrated frontend, committed 60-flight dataset and forced keyword fallback. The test copy uses the existing fixed reference date 2026-10-11; production uses the current IST date. Each case checks request state, clarification/readiness and rendered card count. Missing routes correctly return no results. The empty-input case checks that the UI remains unchanged. No real API key or hosted deployment is tested.", "",
              "| ID | Category | Status | Cards | Result |", "|---|---|---|---|---|"]
    for r in results:
        report.append(f"| {r['id']} | {r['category']} | {r.get('actual',{}).get('status','error')} | {r.get('cards',0)} | {'PASS' if r['passed'] else 'FAIL'} |")
    (ROOT / "docs/ui-chat-report.md").write_text("\n".join(report) + "\n")
    print(f"Full UI acceptance: {passed}/{len(results)} passed.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(run())
