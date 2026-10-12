"""Demo reservations, written for SkyAerovia. No real booking or payment."""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import re
import secrets
import sqlite3

IST = ZoneInfo('Asia/Kolkata')


def normalize_reference(value):
    compact = re.sub(r'[\s-]', '', value.upper()) if isinstance(value, str) else ''
    if not re.fullmatch(r'SKY[0-9A-F]{20}', compact):
        raise ValueError('Enter the complete SKY reference from your demo ticket.')
    return 'SKY-' + '-'.join(compact[i:i + 4] for i in range(3, 23, 4))


def departure_time(flight):
    return datetime.strptime(f'{flight["date"]} {flight["departure"]}', '%Y-%m-%d %H:%M').replace(tzinfo=IST)


def ticket_text(ticket):
    f = ticket['flight']
    return '\n'.join([
        'SKYAEROVIA — DEMO TICKET', 'Simulated reservation. Not valid for travel. No payment was taken.', '',
        'Reference: ' + ticket['reference'], 'Status: ' + ticket['status'].upper(),
        f'Airline: {f["airline"]}', f'Flight: {f["id"]}', f'Route: {f["from"]} → {f["to"]}',
        f'Date: {f["date"]}', f'Time: {f["departure"]} — {f["arrival"]} IST',
        f'Passengers: {ticket["passengers"]}', f'Sample fare per passenger: INR {f["price"]:,}',
        f'Sample total: INR {ticket["total"]:,}', '',
        'Keep this reference to look up or cancel the demo booking.',
        'Demo records may reset when the hosted app restarts or is redeployed.',
    ]) + '\n'


class BookingStore:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS bookings (
                reference TEXT PRIMARY KEY, request_token TEXT NOT NULL UNIQUE,
                flight_json TEXT NOT NULL, passengers INTEGER NOT NULL CHECK(passengers BETWEEN 1 AND 6),
                total INTEGER NOT NULL CHECK(total > 0),
                status TEXT NOT NULL CHECK(status IN ('confirmed','cancelled')),
                created_at TEXT NOT NULL, cancelled_at TEXT
            )''')

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def unpack(row):
        if row is None:
            return None
        return {'reference': row['reference'], 'flight': json.loads(row['flight_json']),
                'passengers': row['passengers'], 'total': row['total'], 'status': row['status'],
                'created_at': row['created_at'], 'cancelled_at': row['cancelled_at']}

    def get(self, reference):
        reference = normalize_reference(reference)
        with self.connect() as db:
            return self.unpack(db.execute('SELECT * FROM bookings WHERE reference = ?', (reference,)).fetchone())

    def create(self, flight, passengers, request_token, now=None):
        if isinstance(passengers, bool) or not isinstance(passengers, int) or not 1 <= passengers <= 6:
            raise ValueError('Choose between 1 and 6 passengers.')
        if not isinstance(request_token, str) or not re.fullmatch(r'[0-9a-f]{32}', request_token):
            raise ValueError('Please select the flight again before confirming.')
        keys = {'id','airline','from','to','date','departure','arrival','price','duration','stops'}
        if not isinstance(flight, dict) or not keys <= flight.keys():
            raise ValueError('Please choose an available demo flight.')
        if any(not isinstance(flight[k],str) or not flight[k] for k in ('id','airline','from','to','date','departure','arrival')):
            raise ValueError('The selected flight has invalid details.')
        for k in ('price','duration','stops'):
            if isinstance(flight[k],bool) or not isinstance(flight[k],int) or flight[k] < (0 if k == 'stops' else 1):
                raise ValueError('The selected flight has invalid details.')
        encoded = json.dumps({k:flight[k] for k in keys}, sort_keys=True, ensure_ascii=False)
        now = now or datetime.now(IST)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            existing = db.execute('SELECT * FROM bookings WHERE request_token = ?', (request_token,)).fetchone()
            if existing:
                if existing['flight_json'] != encoded or existing['passengers'] != passengers:
                    raise ValueError('This confirmation was already used. Please select the flight again.')
                return self.unpack(existing)
            if departure_time(flight) <= now:
                raise ValueError('Choose a flight that departs in the future.')
            for _ in range(5):
                raw = secrets.token_hex(10).upper()
                reference = 'SKY-' + '-'.join(raw[i:i + 4] for i in range(0,20,4))
                try:
                    db.execute('INSERT INTO bookings VALUES (?,?,?,?,?,?,?,NULL)',
                               (reference, request_token, encoded, passengers, flight['price'] * passengers,
                                'confirmed', now.isoformat()))
                except sqlite3.IntegrityError:
                    continue
                return self.unpack(db.execute('SELECT * FROM bookings WHERE reference = ?', (reference,)).fetchone())
            raise RuntimeError('A demo reference could not be created. Please try again.')

    def cancel(self, reference, now=None):
        reference = normalize_reference(reference)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            changed = db.execute("UPDATE bookings SET status = 'cancelled', cancelled_at = ? WHERE reference = ? AND status = 'confirmed'",
                                 ((now or datetime.now(IST)).isoformat(), reference)).rowcount == 1
            ticket = self.unpack(db.execute('SELECT * FROM bookings WHERE reference = ?', (reference,)).fetchone())
            return ticket, changed
