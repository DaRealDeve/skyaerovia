# SkyAerovia
**Your way through the sky** — a student flight-search assistant featuring **Skye**.

**Public demo: [Open SkyAerovia](https://skyaerovia.streamlit.app/)** — deployed and checked on 12 October 2026. The demo is public; the repository and API key remain private.

The app combines Richa's navy/blue interface, Ayman's Gemini extractor with keyword fallback, Sakshi's search logic and 60 simulated flights prepared by Tarun/Codex. It asks for missing details, retains travel preferences, filters by route/date/budget/stops and sorts by price or duration. Flight cards, the logo, loading feedback and a complete chat/filter reset are included. The app can now create simulated demo reservations, download a branded PDF ticket, and cancel a demo ticket after explicit confirmation. It does not create real airline bookings or process payments.

## Run locally
Use Python 3.12 from the project folder:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows, create the environment with `py -m venv .venv` and activate it with `.venv\Scripts\activate`.

The app works without an API key using the keyword fallback. For Gemini, copy `.streamlit/secrets.toml.example` to the ignored `.streamlit/secrets.toml`, fill in the key privately and restart the app. Streamlit Cloud reads the same settings from its Secrets box. Do not commit or paste a real key into chat. `GEMINI_MODEL` is optional; Ayman verified `gemini-3.5-flash` with his private replacement key. Tarun saved the deployment key privately in Streamlit Secrets. Hosted acceptance checks and a Gemini-versus-keyword control passed on 12 October; see `docs/deployment-checks.md`.

## Flight data and search
The live app now supports **32 Indian cities**, **992 routes**, **six daily departures per route**, **six airline display names**, and a rolling **90-day** schedule. It provides **535,680 possible simulated flight options**. Every city pair is available in both directions. The window advances with today's IST date; a fixed route/date option keeps its ID and fare as the window moves. Overnight flights have an explicit next-day arrival date.

All schedules, routes, fares and class/seat availability are fictional student-demo data. They do not assert that a named airline actually flies that route or offers that cabin. Times are IST. New cards show cabin totals including estimated GST, while chat and sidebar budgets still filter the labelled Economy base fare.

Use the route/date form or chat with Skye. Sidebar filters include cabin preference, airline names and departure time. If filters hide all results, the app explains the lowest route base fare and offers to show all options. Out-of-window dates show the supported range. The app never silently changes a requested date/route.

The live compressed route catalog is `flight_catalog.json.gz`; `scripts/generate_catalog.py` regenerates it. `schedule.py` creates only the requested route/day. `city_catalog.py` centralizes supported cities, codes and aliases. The original `flights.json` and `scripts/generate_flights.py` remain historical regression fixtures; they do not limit the live schedule.

## Verification
```sh
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python scripts/run_chat_checks.py
python scripts/run_ui_chat_checks.py
```

Latest upgrade result: **124 tests run, 123 passed, one real-key test skipped**. The booking tests cover class fares and GST rounding, PDF contents, seat conflicts, migration of old records, unique references, repeated/concurrent confirmations, record reopening, invalid IDs, cancellation confirmation, preserved tickets after chat reset, and both book-another choices. All **50/50** fixed-date conversation cases pass both through the integration adapter and the complete Streamlit UI. Tests cover search, extraction, validation, dataset values and dates, filters, follow-ups, reset and HTML escaping. The 50-case fixtures use 2026-10-11 intentionally; production uses today's IST date. The original flight-search regression cases also pass after adding the booking flow.

Ayman supplied a successful real Gemini test screenshot (`source=ai`) on 11 October and Tarun relayed old-key deletion confirmation. No real key was used in the local integration review. For a future key change, verify a local private key without accepting fallback as success:

```sh
python scripts/check_gemini.py --live
```

See `docs/testing-report.md`, `docs/ui-chat-report.md`, `docs/frontend-review.md` and `docs/gemini-live-check.md` for scope and limits.

## Deploy
Use repository **DaRealDeve/skyaerovia**, branch **main**, entry point **app.py**, Python **3.12**, and add the private key under Streamlit Cloud **Advanced settings → Secrets**. Follow `docs/deployment.md` for sign-in, permissions, settings and hosted acceptance checks. The public deployment and hosted acceptance are complete. See `docs/deployment-checks.md` for the dated evidence and its limits.

## Team
The team retains all seven members. Richa supplied the frontend, Sakshi the search module and Ayman the extractor. Tarun/Codex cover Yashvardhan's data, Ayush's QA/API-helper work and Shivam's report/deck/demo work. Contributions are documented without attributing our replacement work to those members.

After the technical checks, Tarun/Codex prepared an eight-page report, editable ten-slide presentation, app screenshots, captioned MP4 walkthrough and presentation script. See `docs/team-responsibilities.md`, `docs/how-it-works.md`, `docs/demo-script.md` and `docs/submission-notes.md`.


## Demo bookings, travel classes and PDF tickets

Use **Find flights** → select **Book demo ticket** → choose Economy, Premium Economy or Business → enter demo passenger names and select seats → **Confirm demo booking**. Each confirmed reservation gets a unique SKY reference and a downloadable PDF ticket with logo, passenger names, class, seats, route, reference and QR code. The app then asks whether you want another ticket, with Yes and No buttons. **My demo tickets** lists tickets created in the current browser session. Clear chat keeps those tickets.

Use **Cancel a ticket** → paste the reference → **Find ticket** → review the details → **Cancel this demo booking** → **Yes, cancel booking**. **Keep my booking** leaves the ticket confirmed. A cancelled ticket stays in the records as Cancelled. The reference can be used from a new session while the server record exists.

Demo reservations use external PostgreSQL when a private `DATABASE_URL` is configured in Streamlit Secrets. These records survive Streamlit restart/redeploy and can be found with the saved reference. `My demo tickets` shows references from the current browser session; use saved-reference lookup after starting a new session. With no database configuration, the app clearly labels its local SQLite fallback as temporary. It never switches to SQLite when a configured PostgreSQL connection fails. The database provider/project must remain available. Older erased temporary records cannot be reconstructed. Use demo passenger names; no passwords, payments or real airline seat inventory are collected. Simulated seats use row-first labels such as 12A (Window), 6C (Aisle) or 1F (Window). A confirmed booking reserves its simulated seats; cancellation releases them. The SKY ID is a demo reference, not an airline PNR.

## Saved working base and next stages

The original working base is preserved at branch **checkpoint/base-2026-10-12**, commit **c6de816cbe36ab1ac3f31eb5fcccbfa03e0dfd05**, plus a separate source ZIP delivered to Tarun. See `docs/upgrade-plan.md` for restoration and scope.

The booking stage is also saved at **checkpoint/booking-2026-10-12**, commit **6a745ea992b9776274792663ae459a91c89e966f**, for rollback before this PDF/class update.

This stage expands routes, dates, airline options and flight cards, and prepares durable PostgreSQL ticket storage. See `docs/expanded-schedule-storage.md`. Login and registration are explicitly last. A new demo video and updated slides are deferred until these features are finished. The old school Python project was used only as a visual feature example; none of its code was read, imported or copied.

## Demo pricing and taxes

The search cards and chat budget refer to the Economy base fare. Booking uses illustrative class multipliers: Economy 1.00, Premium Economy 1.45, Business 2.20. These are demo pricing rules, not airline quotes. The booking screen and PDF show cabin fare, GST, other fees and total. Economy uses 5% GST; Premium Economy and Business use 18%, following the [government GST FAQ, question 59](https://www.pib.gov.in/PressReleasePage.aspx?PRID=2163560&lang=2&reg=48). This estimate covers the current domestic demo routes. Other fees are zero because they have not been modelled; airport and carrier fees are not invented. All amounts are rounded to paise and frozen on confirmation. Older demo tickets retain their original recorded fare.

Quick choices sit directly below Skye's greeting: **Find flights**, **My demo tickets**, **Cancel a ticket**. These open the guided flows. The ticket is a simulated reservation, not an airline boarding pass or tax invoice. See `docs/pdf-ticket-upgrade.md`.

## Persistent database setup

Set `DATABASE_URL` privately in Streamlit Cloud Secrets using the dedicated Neon PostgreSQL connection for this app. Keep the existing Gemini entries. Do not commit the URL or paste the password in chat. `storage.py` sanitizes database failures and uses bound query parameters and atomic seat/booking transactions. The Neon project is on the connected free plan; provider quotas/lifecycle still apply. Login/registration and updated report/PPT/video remain deferred.


### Chat accounts
The opening screen shows only **Register** and **Log in**. Choose **Register** to create an account with a name, email and password (8–128 characters). Choose **Log in** to return; **Log out** ends this app's login. Flight search, route/date selection, Skye chat and ticket controls appear only after successful registration or login. Passwords are never sent to Gemini or appended to chat history.

Neon Managed Auth owns the accounts and password hashing. The Streamlit server calls the branch's documented HTTPS Auth API, keeping the provider session cookie server-side; this avoids third-party-cookie failures in embedded/Safari browsers. The public Auth URL is configuration, not a secret. Provider-signed EdDSA tokens are verified server-side for signature, issuer, audience and expiration. A short-lived token in browser sessionStorage restores the current tab after reload; passwords and provider cookies are not written there. Login may be requested again when that token expires after a reload or when the tab is closed. A live server session can refresh through the provider cookie. Logout removes the browser token and clears app identity; an already-issued JWT has its ordinary expiry window.

A valid login is required before the route form, sidebar, Skye chat or ticket handlers run. Logout returns to the two-choice opening screen and clears this session’s journey history, forms and remembered references; saved database records are retained. New bookings are linked to the verified account ID. My demo tickets loads that account’s saved history from the database on any device. Another account cannot view, download or cancel a linked ticket. Tickets created before ownership was recorded remain unlinked; enter the saved reference once under My demo tickets → Add an older demo ticket to my account. A claimed ticket cannot be reassigned by another account. Cancelled records stay in the account history. History is paginated in groups of 20. Email verification is not enabled for this student demo; an entered email is not proof of email ownership. No social sign-in or password-reset flow is included in this stage.


### Account-ticket migration
Before deploying this version on the existing PostgreSQL database, apply `migrations/001_account_tickets.sql` through the reviewed Neon migration workflow. It adds nullable `owner_user_id` and an owner/history index; all existing rows/fare snapshots/seats/statuses are retained and unassigned. No email/name inference or bulk attribution is used. SQLite local demos add the column and index in their existing local schema initialization. Production runtime does not silently alter an existing table’s ownership schema.

All app ticket operations use an `AccountBookings` facade bound to the server-verified auth subject. Ownership filters apply in SQL to lookup, history and cancellation. Creation includes the owner atomically with the reservation and checks owner consistency on confirmation-token replay. Legacy claim is an atomic update restricted to null-owner rows. Raw/unscoped store operations exist only for trusted migration/legacy fixtures and diagnostics; they are not exposed in the app UI.
