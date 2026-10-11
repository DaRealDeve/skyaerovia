# Ayman's extractor fixes - verified review

Reviewed on 11 October 2026. The attachment extractor..py is stored as extractor.py. No real API key was found in the supplied code.

Ayman's supplied tests were reproduced: 31 passed, one live test skipped. He fixed the agreed output, context replies, Hinglish/typos, explicit stops-allowed preferences and rejected-date/budget diagnostics.

Tarun/Codex added six review regressions and corrections: preserve public fallback metadata; signal unsupported sorting and accept price/duration replies; reject nonfinite AI budgets; correct AI date miscalculations from explicit message dates; keep provider exception bodies out of logs/diagnostics; remove an unverified model-retirement comment.

Fixes branch validation: 49 tests run, 48 passed and one live test skipped (11 search, 31 supplied offline extractor and 6 review tests).

Combined integration validation: 74 tests run, 73 passed and one live test skipped. All 50 specified offline chat cases pass. Integration now reads result.problems, clears rejected saved fields and asks for valid dates/budgets/sorting choices. Integration changes live in the separate integration draft.

Live Gemini is PENDING a private replacement key. No exposed key was used. Network/quota/timeout/malformed-response tests use mocks. Fixed offline reference date: 2026-10-11. Yearless dates use the current year and past dates are not silently moved to next year. Ambiguous past-tense kal/parso asks for clarification.
