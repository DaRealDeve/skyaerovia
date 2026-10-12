# Expanded schedules, interface and persistent tickets

The old 60-flight JSON remains a historical regression fixture. The live app uses flight_catalog.json.gz: 5,952 daily departure templates across all 992 directed routes between 32 Indian cities. Each route has six departure times and six airline display names, with four nonstop and two one-stop options. All routes, schedules, fares, stop counts, cabin offerings and seat layouts are fictional student-demo data, including routes not actually flown by a named carrier. These are not live availability or airline offers.

The 90-day window starts on today's IST date and advances at runtime. Only the requested route/day is materialized, avoiding a huge in-memory table. This supplies 535,680 possible simulated flight options without rendering/loading that many records. IDs and fares for a given route/date/template remain stable when the window advances. Overnight arrival_date is separate from departure date and is retained in booking/PDF snapshots. scripts/generate_catalog.py reproduces the compressed catalog. City names, airport codes and aliases share city_catalog.py.

The frontend now includes a direct route/date form, preferred cabin, airline and departure-time filters, clearer time/route cards and per-passenger class totals including GST. Budget filters still apply to Economy base fare and are labelled accordingly. If filters hide results, the app explains the lowest available base fare and offers Show all flights on this route; it does not silently change the requested date or route. An out-of-window date shows the actual supported range. Past departures cannot be newly booked.

## Persistent ticket storage

The app uses PostgreSQL when a private DATABASE_URL is configured in Streamlit Secrets or environment. It never falls back to temporary SQLite if a configured database is unavailable; it shows a safe storage error instead. New connections retrieve the same saved ticket, fare, status and seats. Confirmation/cancellation transactions hold a brief PostgreSQL transaction lock, preventing duplicate reservations and competing seat allocation across app processes. Cancellation retains the booking record and releases the seat. Paise pricing remains frozen. Queries use bound parameters; database error details are not shown publicly.

Neon free-plan project skyaerovia-tickets was prepared for this app. This is external storage and is unaffected by restarting/redeploying Streamlit. The provider/project must remain available; free-plan limits and provider account lifecycle still apply. No account/login system has been added. My demo tickets lists this browser session's references; reopening the app or a new session may require saved-reference lookup. Possession of the high-entropy reference is the guest lookup/cancellation mechanism. Use demo names, not sensitive passenger identity documents. No payments.

The pre-PostgreSQL tickets were temporary. New durable storage cannot reconstruct a record already erased by an earlier Streamlit restart. Code checkpoints and source ZIPs do not include private credentials or database records. DATABASE_URL must remain private and must not be committed.

## Rollback and later work

Before this stage, checkpoint/pdf-tickets-2026-10-12 preserved d62c70ba03ae847a656fb3930f414f4badac32a9. The original base and first booking-stage checkpoints also remain. Restoring earlier source cannot make its old SQLite mode use PostgreSQL automatically; keep durable database records intact and adapt the storage module if reverting UI/data alone.

Login/registration and updated report/PPT/video are deferred. The old school project was not read or reused. Hosted checks and exact test results are recorded after deployment.
