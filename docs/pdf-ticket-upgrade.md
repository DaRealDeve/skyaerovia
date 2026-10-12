# PDF tickets and cabin choices - 12 October 2026

After selecting a simulated flight, choose Economy, Premium Economy or Business, enter 1-6 demo passenger names and select distinct seats. Labels such as 12A are row-first and show Window/Aisle/Middle. Cabin layouts and prices are illustrative. Confirmation reserves those simulated seats atomically; competing guests cannot hold the same seat on the same flight/class. Cancellation releases them and retains the cancelled record. Repeated confirmation returns the existing booking.

The three actions are vertical blue choices inside Skye's first assistant message, below the greeting. Find flights opens search; My demo tickets opens this session's reservations; Cancel a ticket opens reference lookup and confirmation.

PDF download replaces the text download. The original landscape layout includes supplied logo, route/airport codes, airline, flight ID, travel date/times, class, passenger names/seats, full reference, a QR containing only that reference, status and fare breakdown. It does not invent a boarding time, airport gate or check-in. It explicitly says SIMULATED RESERVATION / NOT VALID FOR TRAVEL. No payment is taken. A cancelled PDF retains the original fare and shows Cancelled.

## Fare estimates

Search card prices and budget filters remain Economy base fares. Booking applies illustrative multipliers (1.00, 1.45, 2.20), then rounds amounts to paise using Decimal HALF_UP. GST is 5% for Economy and 18% for the two non-Economy choices, based on the official government FAQ question 59: https://www.pib.gov.in/PressReleasePage.aspx?PRID=2163560&lang=2&reg=48 (checked 12 October 2026). This is an estimate for the current domestic demo routes, not a tax invoice. Other fees are 0 because they are not modelled; no airport/airline fee or additional tax is invented. The quote is frozen on confirmation. Migrated pre-update records keep their original fare and say GST was not recorded.

## Storage and rollback

Guest records and simulated seat holds are in ignored .data/bookings.sqlite3. Cloud storage is temporary and may reset on restart/redeployment. A saved reference can locate a record while it exists. No accounts or payment details are used. Use demo names; English names up to 60 characters are supported by this ticket version.

Rollback source: checkpoint/booking-2026-10-12 at 6a745ea992b9776274792663ae459a91c89e966f. The original search-only base checkpoint also remains available. Neither restoration restores temporary booking data. Do not include the database or API key in source backups.

## Validation

112 unittest checks: 111 pass and one live-key test skipped locally. Covers class prices/tax rounding, invalid input, repeated requests, concurrent seat conflict, cancellation release, PDF reference/name/class/seat/amount/status, old database migration and Streamlit flows. Deterministic adapter corpus 50/50; full Streamlit UI corpus 50/50. The PDF is rendered and visually inspected for ordinary and six-passenger tickets. Local browser and hosted download checks are recorded separately after publication. These checks do not guarantee every possible input or a live Gemini call.

Login/registration and updated video/PPT are deferred. The school Python file was not read or reused.
