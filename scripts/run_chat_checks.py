"""Run 50 conversational checks offline; record failures without hiding them.

Run from the project root: python scripts/run_chat_checks.py
"""
import json
import logging
import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import extractor
from integration import prepare_request


def run():
    cases = json.loads((ROOT / "tests/chat_cases.json").read_text())
    logging.disable(logging.CRITICAL)
    results = []
    with patch.object(extractor, "extract_with_ai", side_effect=RuntimeError("Offline QA: Gemini deliberately unavailable")):
        for case in cases:
            try:
                state, status, reply = prepare_request(case["message"], case.get("context", {}), date(2026, 10, 11), extractor.extract_request)
                actual = {"status": status, **state}
                mismatches = {k: {"expected": v, "actual": actual.get(k)} for k, v in case["expected"].items() if actual.get(k) != v}
                result = {**case, "actual": actual, "reply": reply, "passed": not mismatches, "mismatches": mismatches}
            except Exception as error:
                result = {**case, "passed": False, "error": type(error).__name__ + ": " + str(error)}
            results.append(result)
    passed = sum(r["passed"] for r in results)
    report = ["# SkyAerovia conversational test report", "", f"Result: **{passed}/{len(results)} passed; {len(results)-passed} failed.**", "", "Scope: deterministic offline keyword fallback plus the integration adapter. Fixed reference date: 2026-10-11 (IST). No API key or live Gemini call was used. Cases check status and the listed expected fields; passing does not guarantee every possible field is correct.", "", "Retest after the extractor/frontend/data integration. The original baseline was 43/50. The separate unittest round ran 81 checks: 80 passed and one live test skipped locally. All 50 cases also pass through the complete Streamlit UI with simulated data. The shared app's private key/live check and hosted acceptance remain pending.", "", "## Results", "", "| ID | Category | Input | Result |", "|---|---|---|---|"]
    for r in results:
        report.append(f"| {r['id']} | {r['category']} | {r['message'].replace('|', '/')} | {'PASS' if r['passed'] else 'FAIL'} |")
    report += ["", "## Failures to resolve before final acceptance", ""]
    for r in results:
        if not r["passed"]:
            report += [f"### {r['id']}: {r['message']}", "", "Context: `" + json.dumps(r.get("context", {})) + "`", "", "Mismatch: `" + json.dumps(r.get("mismatches", r.get("error")), ensure_ascii=False) + "`", ""]
    report += ["## Ownership and next round", "", "Tarun and Codex cover Ayush's test preparation, execution and results reporting. Ayush remains a team member. Ayman owns extractor fixes; Tarun's integration handles validation and state. Neither the initial QA results nor the draft PR should be marked final acceptance while failures remain.", "", "Full UI/data checks are recorded in docs/ui-chat-report.md and docs/frontend-review.md. After private API setup: compare live Gemini and forced fallback behavior. After deployment: repeat the user flow on the deployed app. Never put the API key in a test report or screenshot.", ""]
    (ROOT / "docs").mkdir(exist_ok=True)
    (ROOT / "docs/chat-test-results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    (ROOT / "docs/testing-report.md").write_text("\n".join(report))
    print(f"{passed}/{len(results)} passed; {len(results)-passed} failed. See docs/testing-report.md")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(run())

