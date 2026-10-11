"""Generate fictional flight data for the SkyAerovia student demo.

Run from the project folder: python scripts/generate_flights.py
Optional: python scripts/generate_flights.py --start-date 2026-10-12
All times are IST. These are sample schedules and fares, not live airline offers.
"""
import argparse
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IST = timezone(timedelta(hours=5, minutes=30))
ROUTES = (
    ("Delhi", "Mumbai", 130),
    ("Mumbai", "Bengaluru", 120),
    ("Bengaluru", "Chennai", 60),
    ("Chennai", "Hyderabad", 80),
    ("Hyderabad", "Kolkata", 120),
    ("Kolkata", "Pune", 145),
    ("Pune", "Ahmedabad", 85),
    ("Ahmedabad", "Delhi", 90),
)
AIRLINES = ("IndiGo", "Air India", "Akasa Air")


def generate(start):
    flights = []

    def add(day, origin, destination, departure, duration, stops, price, airline):
        departure_time = datetime.combine(day, datetime.strptime(departure, "%H:%M").time())
        arrival_time = departure_time + timedelta(minutes=duration)
        if arrival_time.date() != day:
            raise ValueError("Demo flights must arrive on the departure date")
        flights.append({
            "id": f"SKY-DEMO-{day:%Y%m%d}-{len(flights) + 1:03d}",
            "airline": airline, "from": origin, "to": destination,
            "date": day.isoformat(), "departure": departure,
            "arrival": arrival_time.strftime("%H:%M"), "duration": duration,
            "stops": stops, "price": price,
        })

    for offset in range(7):
        day = start + timedelta(days=offset)
        for index, (origin, destination, nonstop_duration) in enumerate(ROUTES):
            stops = int((offset + index) % 4 == 0)
            departure_minutes = 6 * 60 + 15 + index * 65 + offset * 10
            departure = f"{departure_minutes // 60:02d}:{departure_minutes % 60:02d}"
            add(day, origin, destination, departure,
                nonstop_duration + (100 if stops else 0), stops,
                4100 + index * 350 + offset * 180 - stops * 500,
                AIRLINES[(offset + index) % len(AIRLINES)])
        if offset == 1:
            add(day, "Delhi", "Mumbai", "11:20", 140, 0, 3900, "Air India")
            add(day, "Delhi", "Mumbai", "14:10", 265, 1, 3200, "IndiGo")
            add(day, "Mumbai", "Delhi", "16:15", 125, 0, 4600, "Akasa Air")
        if offset == 3:
            add(day, "Bengaluru", "Kolkata", "18:00", 165, 0, 6100, "Air India")
    return flights


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", type=date.fromisoformat,
                        default=datetime.now(IST).date(), help="First date (YYYY-MM-DD); defaults to today in IST")
    args = parser.parse_args()
    path = ROOT / "flights.json"
    path.write_text(json.dumps(generate(args.start_date), indent=2) + "\n", encoding="utf-8")
    print(f"Created 60 simulated flights for {args.start_date} through {args.start_date + timedelta(days=6)}.")


if __name__ == "__main__":
    main()
