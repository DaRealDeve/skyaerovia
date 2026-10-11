# Full-interface conversation checks

Result: **50/50 passed.**

Scope: Richa's integrated frontend, committed 60-flight dataset and forced keyword fallback. The test copy uses the existing fixed reference date 2026-10-11; production uses the current IST date. Each case checks request state, clarification/readiness and rendered card count. Missing routes correctly return no results. The empty-input case checks that the UI remains unchanged. No real API key or hosted deployment is tested.

| ID | Category | Status | Cards | Result |
|---|---|---|---|---|
| T01 | Normal route | ready | 1 | PASS |
| T02 | Normal route | ready | 1 | PASS |
| T03 | Normal route | ready | 1 | PASS |
| T04 | Normal route | ready | 1 | PASS |
| T05 | Normal route | ready | 1 | PASS |
| T06 | Normal route | ready | 1 | PASS |
| T07 | Normal route | ready | 1 | PASS |
| T08 | Normal route | ready | 1 | PASS |
| T09 | City alias | ready | 0 | PASS |
| T10 | City alias | ready | 1 | PASS |
| T11 | City alias | ready | 0 | PASS |
| T12 | City alias | ready | 0 | PASS |
| T13 | Date | ready | 0 | PASS |
| T14 | Date | ready | 1 | PASS |
| T15 | Date | ready | 3 | PASS |
| T16 | Date | ready | 1 | PASS |
| T17 | Date | ready | 1 | PASS |
| T18 | Date | ready | 1 | PASS |
| T19 | Date | ready | 3 | PASS |
| T20 | Budget | ready | 1 | PASS |
| T21 | Budget | ready | 1 | PASS |
| T22 | Budget | ready | 1 | PASS |
| T23 | Budget | ready | 1 | PASS |
| T24 | Invalid budget | clarify | 0 | PASS |
| T25 | Sorting | ready | 1 | PASS |
| T26 | Sorting | ready | 1 | PASS |
| T27 | Unsupported sorting | clarify | 0 | PASS |
| T28 | Stops | ready | 0 | PASS |
| T29 | Stops | ready | 0 | PASS |
| T30 | Stops | ready | 0 | PASS |
| T31 | Clear nonstop preference | ready | 1 | PASS |
| T32 | Missing details | clarify | 0 | PASS |
| T33 | Missing details | clarify | 0 | PASS |
| T34 | Missing details | clarify | 0 | PASS |
| T35 | Empty message | help | 0 | PASS |
| T36 | Follow-up city | ready | 1 | PASS |
| T37 | Follow-up city | ready | 1 | PASS |
| T38 | Follow-up date | ready | 1 | PASS |
| T39 | Follow-up sorting | ready | 1 | PASS |
| T40 | Follow-up budget | ready | 1 | PASS |
| T41 | Hinglish | ready | 1 | PASS |
| T42 | Hinglish | ready | 0 | PASS |
| T43 | Hinglish | ready | 1 | PASS |
| T44 | Hinglish | ready | 1 | PASS |
| T45 | Hinglish preference | ready | 1 | PASS |
| T46 | City typo | clarify | 0 | PASS |
| T47 | Date typo | ready | 1 | PASS |
| T48 | Past date | clarify | 0 | PASS |
| T49 | Invalid date | clarify | 0 | PASS |
| T50 | Unsupported city | clarify | 0 | PASS |
