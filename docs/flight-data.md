# Simulated flight data

Tarun and Codex cover Yashvardhan's data deliverable, following Tarun's instruction on 12 October 2026. Yashvardhan remains in the team. This file does not attribute the dataset implementation to him.

The committed flights.json contains 60 fictional flights for 12–18 October 2026 inclusive. All eight supported cities appear as origins and destinations: Delhi, Mumbai, Bengaluru, Chennai, Hyderabad, Kolkata, Pune and Ahmedabad. Eight sample routes appear each day; four additional flights provide alternative choices and a return route.

Each record has exactly id, airline, from, to, date, departure, arrival, duration, stops and price. IDs are unique. Dates use YYYY-MM-DD, times use HH:MM in IST, durations are integer minutes, stops are 0 or 1 and fares are integer INR. Every arrival is on the departure date and agrees with the stated duration. Connecting-flight duration includes the fictional layover.

Airline names identify sample records only. Routes, schedules, IDs and fares are invented for the student prototype; they do not describe bookable flights or current airline offerings. The app labels these results as simulated.

## Keep the dates current

From the project folder, run:

```sh
python scripts/generate_flights.py
```

This replaces flights.json with 60 demo records for today in IST through six days later. Commit the refreshed JSON to the integration branch and rerun tests before the demo. The deployment reads the committed dataset; dates do not refresh automatically.

For reproducible data, use an explicit first date:

```sh
python scripts/generate_flights.py --start-date 2026-10-12
```

Tomorrow relative to the first date has three Delhi–Mumbai choices: two nonstop flights and one cheaper connecting flight. Price/duration sorting, a ₹5,000 budget, nonstop filtering and an empty-result budget are covered by the dataset tests. The generator is also checked across month/year and leap-day boundaries.
