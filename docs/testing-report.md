# SkyAerovia conversational test report

Result: **50/50 passed; 0 failed.**

Scope: deterministic offline keyword fallback plus the integration adapter. Fixed reference date: 2026-10-11 (IST). No API key or live Gemini call was used. Cases check status and the listed expected fields; passing does not guarantee every possible field is correct.

Retest after the extractor/frontend/data integration. The original baseline was 43/50. The expanded schedule/storage unittest round ran 124 checks: 123 passed and one live test skipped locally. All 50 cases also pass through the complete Streamlit UI with simulated data. Hosted acceptance and a semantic Gemini-versus-keyword control passed on 12 October 2026; see docs/deployment-checks.md. This offline run does not make a live API call.

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
| T24 | Invalid budget | Delhi to Mumbai tomorrow under -100 | PASS |
| T25 | Sorting | cheapest Delhi to Mumbai tomorrow | PASS |
| T26 | Sorting | fastest Delhi to Mumbai tomorrow | PASS |
| T27 | Unsupported sorting | earliest Delhi to Mumbai tomorrow | PASS |
| T28 | Stops | nonstop flights Delhi to Mumbai tomorrow | PASS |
| T29 | Stops | direct flights Delhi to Mumbai tomorrow | PASS |
| T30 | Stops | no layovers flights Delhi to Mumbai tomorrow | PASS |
| T31 | Clear nonstop preference | Delhi to Mumbai tomorrow, stops are fine | PASS |
| T32 | Missing details | from Delhi | PASS |
| T33 | Missing details | flights to Mumbai tomorrow | PASS |
| T34 | Missing details | Delhi to Mumbai | PASS |
| T35 | Empty message |  | PASS |
| T36 | Follow-up city | Mumbai | PASS |
| T37 | Follow-up city | Delhi | PASS |
| T38 | Follow-up date | tomorrow | PASS |
| T39 | Follow-up sorting | the cheapest | PASS |
| T40 | Follow-up budget | 5000 | PASS |
| T41 | Hinglish | Delhi se Mumbai kal | PASS |
| T42 | Hinglish | Delhi to Mumbai aaj | PASS |
| T43 | Hinglish | Dilli se Mumbai tomorrow | PASS |
| T44 | Hinglish | 5000 se kam | PASS |
| T45 | Hinglish preference | layover chalega | PASS |
| T46 | City typo | Delih to Mumbai tomorrow | PASS |
| T47 | Date typo | Delhi to Mumbai tomorow | PASS |
| T48 | Past date | Delhi to Mumbai 2026-10-05 | PASS |
| T49 | Invalid date | Delhi to Mumbai 2026-02-30 | PASS |
| T50 | Unsupported city | Delhi to London tomorrow | PASS |

## Failures to resolve before final acceptance

## Ownership and next round

Tarun and Codex cover Ayush's test preparation, execution and results reporting. Ayush remains a team member. Ayman owns extractor fixes; Tarun's integration handles validation and state. Neither the initial QA results nor the draft PR should be marked final acceptance while failures remain.

Full UI/data checks are recorded in docs/ui-chat-report.md and docs/frontend-review.md. Dated hosted checks and the Gemini/keyword comparison are in docs/deployment-checks.md. Repeat hosted acceptance after material code, data or API configuration changes. Never put the API key in a test report or screenshot.
