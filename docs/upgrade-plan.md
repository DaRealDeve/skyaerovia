# SkyAerovia upgrade plan — 12 October 2026

## Saved working base

- GitHub branch: checkpoint/base-2026-10-12
- Baseline commit: c6de816cbe36ab1ac3f31eb5fcccbfa03e0dfd05
- Separate source ZIP: SkyAerovia_Base_2026-10-12.zip, delivered to Tarun.

The GitHub checkpoint holds the exact original source tree. To restore the app, create a new main commit using that saved tree, or point Streamlit at the saved branch while keeping Python 3.12 and the current private Secrets. Restoring source code does not restore guest demo bookings. Do not commit the private API key or database file.

## First stage: implemented together by Tarun and Codex

1. Fresh demo reservation storage and a unique, random SKY reference for each booking.
2. Review selected flight and 1–6 passengers before creating the demo ticket. Reference download included.
3. Duplicate/repeated confirmation requests return the same ticket rather than creating extra records.
4. “Book another ticket?” Yes returns to results/search; No opens the current session's tickets.
5. Find/cancel by saved reference, review before confirmation, and Keep my booking option.
6. Cancelled records remain visible; repeating cancellation does not change the original cancellation time or other bookings.
7. Quick options: Find flights, My demo tickets and Cancel a ticket. Cancellation chat requests open the guided flow. Clear chat preserves tickets.

These are simulated reservations, not airline tickets. No payment or refund occurs. Demo SQLite data can disappear after hosted restart/redeployment. Keep the reference download. Permanent database storage and user ownership will be designed before the later account phase.

## Next stages in the agreed order

- More departure cities and destinations, with consistent search, extraction and simulated data.
- Economy, Premium Economy and Business booking choices: implemented in the PDF ticket stage; search budgets still use base fares.
- More airlines and flight choices.
- Larger frontend improvements. Row-first seat selection with window/aisle descriptions is implemented; the old A1–A10 pattern was not reused.
- Login and registration last, with suitable permanent storage and secure ownership.

No school-project code, bus/car modes, old plaintext-password pattern or legacy seat list was reused.

## Verification for this stage

- Combined unittest run: 97 checks, 96 passed, 1 live-private-key check skipped locally.
- Existing deterministic adapter corpus: 50/50 pass.
- Existing full Streamlit UI corpus: 50/50 pass.
- New coverage includes concurrent/repeated confirmations, unique references, preserved snapshots, invalid/unknown IDs, cancelled status, confirmation versus keeping a booking, both more-ticket choices, a new browser session and chat-triggered cancellation.

Manual local browser checks passed: a two-passenger INR 7,800 booking, reference generation, actual text-ticket download, No returning to the ticket list, Keep my booking preserving Confirmed status, and final cancellation displaying Cancelled. Hosted evidence is recorded after publication. These results do not assert that errors are impossible or that 50 cases were tested against live Gemini.

## PDF ticket stage

Saved previous stage: **checkpoint/booking-2026-10-12** at **6a745ea992b9776274792663ae459a91c89e966f**. To restore, make a new main commit using its tree or temporarily point Streamlit at that checkpoint branch. Leave the private Secrets unchanged. Source restoration does not restore temporary demo reservations.

Implemented: three booking classes; simulated reserved seats and release on cancellation; original logo-branded PDF downloads; fixed fare/GST snapshots; vertical actions under Skye's greeting. Verification: 112 tests, 111 pass, one private-key check skipped locally; adapter 50/50 and full UI 50/50. Details are in `pdf-ticket-upgrade.md`.

Login/registration, the next video and updated PPT remain deferred at Tarun's request.
