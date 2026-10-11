# SkyAerovia conversational test report

Result: **43/50 passed; 7 failed.**

Scope: deterministic offline keyword fallback plus the draft integration adapter. Fixed reference date: 2026-10-11 (IST). No API key or live Gemini call was used. Cases check status and the listed expected fields; passing does not guarantee every possible field is correct.

This is an initial test round. Live Gemini, the team's flight dataset, final UI and deployed-app testing remain pending. The existing 26 automated search/integration/UI checks passed separately.

## Results

| ID | Category | Input | Result |
|---|---|---|---|
| T01 | Normal route | flights from Delhi to Mumbai tomorrow | PASS |
| T02 | Normal route | flights from Mumbai to Bengaluru tomorrow | PASS |
| T03 | Normal route | flights from Bengaluru to Chennai tomorrow | PASS |
| T04 | Normal route | flights from Chennai to Hyderabad tomorrow | PASS |
| T05 | Normal route | flights from Hyderabad to Kolkata tomorrow | PASS |
| T06 | Normal route | flights from Kolkata to Pune tomorrow | PASS |
| T07 | Normal route | flights from Pune to Ahmedabad tomorrow | PASS |
| T08 | Normal route | flights from Ahmedabad to Delhi tomorrow | PASS |
| T09 | City alias | Bangalore to Bombay tomorrow | PASS |
| T10 | City alias | DEL to BOM tomorrow | PASS |
| T11 | City alias | New Delhi to Calcutta tomorrow | PASS |
| T12 | City alias | Madras to Poona tomorrow | PASS |
| T13 | Date | Delhi to Mumbai today | PASS |
| T14 | Date | Delhi to Mumbai tomorrow | PASS |
| T15 | Date | Delhi to Mumbai day after tomorrow | PASS |
| T16 | Date | Delhi to Mumbai tmrw | PASS |
| T17 | Date | Delhi to Mumbai next friday | PASS |
| T18 | Date | Delhi to Mumbai 15 oct | PASS |
| T19 | Date | Delhi to Mumbai 2026-10-13 | PASS |
| T20 | Budget | Delhi to Mumbai tomorrow under 5k | PASS |
| T21 | Budget | Delhi to Mumbai tomorrow below 4500 | PASS |
| T22 | Budget | Delhi to Mumbai tomorrow max Rs 6,000 | PASS |
| T23 | Budget | Delhi to Mumbai tomorrow within 1 lakh | PASS |
| T24 | Invalid budget | Delhi to Mumbai tomorrow under -100 | FAIL |
| T25 | Sorting | cheapest Delhi to Mumbai tomorrow | PASS |
| T26 | Sorting | fastest Delhi to Mumbai tomorrow | PASS |
| T27 | Unsupported sorting | earliest Delhi to Mumbai tomorrow | PASS |
| T28 | Stops | nonstop flights Delhi to Mumbai tomorrow | PASS |
| T29 | Stops | direct flights Delhi to Mumbai tomorrow | PASS |
| T30 | Stops | no layovers flights Delhi to Mumbai tomorrow | PASS |
| T31 | Clear nonstop preference | Delhi to Mumbai tomorrow, stops are fine | FAIL |
| T32 | Missing details | from Delhi | PASS |
| T33 | Missing details | flights to Mumbai tomorrow | PASS |
| T34 | Missing details | Delhi to Mumbai | PASS |
| T35 | Empty message |  | PASS |
| T36 | Follow-up city | Mumbai | PASS |
| T37 | Follow-up city | Delhi | PASS |
| T38 | Follow-up date | tomorrow | PASS |
| T39 | Follow-up sorting | the cheapest | PASS |
| T40 | Follow-up budget | 5000 | FAIL |
| T41 | Hinglish | Delhi se Mumbai kal | FAIL |
| T42 | Hinglish | Delhi to Mumbai aaj | FAIL |
| T43 | Hinglish | Dilli se Mumbai tomorrow | PASS |
| T44 | Hinglish | 5000 se kam | PASS |
| T45 | Hinglish preference | layover chalega | FAIL |
| T46 | City typo | Delih to Mumbai tomorrow | PASS |
| T47 | Date typo | Delhi to Mumbai tomorow | FAIL |
| T48 | Past date | Delhi to Mumbai 2026-10-05 | PASS |
| T49 | Invalid date | Delhi to Mumbai 2026-02-30 | PASS |
| T50 | Unsupported city | Delhi to Goa tomorrow | PASS |

## Failures to resolve before final acceptance

### T24: Delhi to Mumbai tomorrow under -100

Context: `{}`

Mismatch: `{"status": {"expected": "clarify", "actual": "ready"}}`

### T31: Delhi to Mumbai tomorrow, stops are fine

Context: `{"intent": "search", "origin": "Delhi", "destination": "Mumbai", "date": "2026-10-12", "non_stop": true}`

Mismatch: `{"non_stop": {"expected": false, "actual": true}}`

### T40: 5000

Context: `{"intent": "search", "origin": "Delhi", "destination": "Mumbai", "date": "2026-10-12", "asking": "max_price"}`

Mismatch: `{"status": {"expected": "ready", "actual": "help"}, "max_price": {"expected": 5000, "actual": null}}`

### T41: Delhi se Mumbai kal

Context: `{}`

Mismatch: `{"status": {"expected": "ready", "actual": "clarify"}, "destination": {"expected": "Mumbai", "actual": null}, "date": {"expected": "2026-10-12", "actual": null}}`

### T42: Delhi to Mumbai aaj

Context: `{}`

Mismatch: `{"status": {"expected": "ready", "actual": "clarify"}, "date": {"expected": "2026-10-11", "actual": null}}`

### T45: layover chalega

Context: `{"intent": "search", "origin": "Delhi", "destination": "Mumbai", "date": "2026-10-12", "non_stop": true}`

Mismatch: `{"status": {"expected": "ready", "actual": "help"}, "non_stop": {"expected": false, "actual": true}}`

### T47: Delhi to Mumbai tomorow

Context: `{}`

Mismatch: `{"status": {"expected": "ready", "actual": "clarify"}}`

## Ownership and next round

Tarun and Codex cover Ayush's test preparation, execution and results reporting. Ayush remains a team member. Ayman owns extractor fixes; Tarun's integration handles validation and state. Neither the initial QA results nor the draft PR should be marked final acceptance while failures remain.

After fixes: rerun this script and the unittest suite. After flight data and final UI arrive: test all cases through the app and check actual routes, dates, prices, filters and reset. After private API setup: compare live Gemini and forced fallback behavior. After deployment: repeat the user flow on the deployed app. Never put the API key in a test report or screenshot.
