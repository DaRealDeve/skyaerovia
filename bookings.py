"""Guest demo bookings with fixed fare snapshots and simulated seat reservations."""
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import json
import re
import secrets
import sqlite3
from fares import fare_quote, cabin_seats

IST=ZoneInfo('Asia/Kolkata')


def normalize_reference(value):
    compact=re.sub(r'[\s-]','',value.upper()) if isinstance(value,str) else ''
    if not re.fullmatch(r'SKY[0-9A-F]{20}',compact):
        raise ValueError('Enter the complete SKY reference from your demo ticket.')
    return 'SKY-'+'-'.join(compact[i:i+4] for i in range(3,23,4))


def departure_time(flight):
    return datetime.strptime(f'{flight["date"]} {flight["departure"]}','%Y-%m-%d %H:%M').replace(tzinfo=IST)


def validate_names(names, passengers):
    if names is None:return [f'Guest {i+1}' for i in range(passengers)]
    if not isinstance(names,list) or len(names)!=passengers:
        raise ValueError('Enter a demo name for each passenger.')
    normalized=[]
    for name in names:
        if not isinstance(name,str):raise ValueError('Enter a valid passenger name.')
        name=' '.join(name.split())
        if not name or len(name)>60 or not re.fullmatch(r"[A-Za-z0-9 .'-]+",name):
            raise ValueError('Use 1-60 English letters, numbers, spaces, apostrophes or hyphens for demo names.')
        normalized.append(name)
    return normalized


class BookingStore:
    integrity_error=sqlite3.IntegrityError
    def __init__(self,path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('''CREATE TABLE IF NOT EXISTS bookings (
                reference TEXT PRIMARY KEY, request_token TEXT NOT NULL UNIQUE,
                flight_json TEXT NOT NULL, passengers INTEGER NOT NULL CHECK(passengers BETWEEN 1 AND 6),
                total NUMERIC NOT NULL CHECK(total > 0),
                status TEXT NOT NULL CHECK(status IN ('confirmed','cancelled')),
                created_at TEXT NOT NULL, cancelled_at TEXT,
                cabin TEXT NOT NULL DEFAULT 'Economy', names_json TEXT,
                seats_json TEXT, pricing_json TEXT)''')
            columns={r['name'] for r in db.execute('PRAGMA table_info(bookings)')}
            for column,definition in (('cabin',"TEXT NOT NULL DEFAULT 'Economy'"),('names_json','TEXT'),('seats_json','TEXT'),('pricing_json','TEXT')):
                if column not in columns:db.execute(f'ALTER TABLE bookings ADD COLUMN {column} {definition}')
            db.execute('''CREATE TABLE IF NOT EXISTS seat_holds (
                flight_id TEXT NOT NULL,cabin TEXT NOT NULL,seat TEXT NOT NULL,reference TEXT NOT NULL,
                PRIMARY KEY(flight_id,cabin,seat),FOREIGN KEY(reference) REFERENCES bookings(reference))''')

    @contextmanager
    def connect(self):
        db=sqlite3.connect(self.path,timeout=10);db.row_factory=sqlite3.Row
        db.execute('PRAGMA foreign_keys = ON')
        try:
            with db:yield db
        finally:db.close()

    @staticmethod
    def unpack(row):
        if row is None:return None
        f=json.loads(row['flight_json']);n=row['passengers']
        pricing=json.loads(row['pricing_json']) if row['pricing_json'] else {
            'version':1,'cabin':row['cabin'],'passengers':n,
            'base_per_person_paise':int(round(row['total']*100/n)),
            'subtotal_paise':int(round(row['total']*100)),
            'gst_percent':0,'gst_paise':0,'other_fees_paise':0,'total_paise':int(round(row['total']*100)),
            'note':'Original pre-update fare retained. GST and seats were not recorded for this older demo ticket.'}
        return {'reference':row['reference'],'flight':f,'passengers':n,
                'total':pricing['total_paise']/100,'status':row['status'],
                'created_at':row['created_at'],'cancelled_at':row['cancelled_at'],'cabin':row['cabin'],
                'passenger_names':json.loads(row['names_json']) if row['names_json'] else [f'Guest {i+1}' for i in range(n)],
                'seats':json.loads(row['seats_json']) if row['seats_json'] else [],'pricing':pricing}

    def get(self,reference):
        reference=normalize_reference(reference)
        with self.connect() as db:
            return self.unpack(db.execute('SELECT * FROM bookings WHERE reference = ?',(reference,)).fetchone())

    def available_seats(self,flight_id,cabin):
        layout=cabin_seats(cabin)
        with self.connect() as db:
            taken={r['seat'] for r in db.execute('SELECT seat FROM seat_holds WHERE flight_id = ? AND cabin = ?',(flight_id,cabin))}
        return [seat for seat in layout if seat not in taken]

    def create(self,flight,passengers,request_token,now=None,*,cabin='Economy',passenger_names=None,seats=None):
        if isinstance(passengers,bool) or not isinstance(passengers,int) or not 1<=passengers<=6:
            raise ValueError('Choose between 1 and 6 passengers.')
        if not isinstance(request_token,str) or not re.fullmatch(r'[0-9a-f]{32}',request_token):
            raise ValueError('Please select the flight again before confirming.')
        keys={'id','airline','from','to','date','departure','arrival','price','duration','stops'}
        if not isinstance(flight,dict) or not keys<=flight.keys():raise ValueError('Please choose an available demo flight.')
        if any(not isinstance(flight[k],str) or not flight[k] for k in ('id','airline','from','to','date','departure','arrival')):
            raise ValueError('The selected flight has invalid details.')
        for k in ('price','duration','stops'):
            if isinstance(flight[k],bool) or not isinstance(flight[k],int) or flight[k]<(0 if k=='stops' else 1):
                raise ValueError('The selected flight has invalid details.')
        layout=cabin_seats(cabin);names=validate_names(passenger_names,passengers)
        if seats is not None and (not isinstance(seats,list) or len(seats)!=passengers or any(not isinstance(s,str) for s in seats) or len(set(seats))!=passengers or any(s not in layout for s in seats)):
            raise ValueError('Choose a different available seat for every passenger.')
        snapshot={k:flight[k] for k in keys}
        if 'arrival_date' in flight:
            snapshot['arrival_date']=flight['arrival_date']
        encoded=json.dumps(snapshot,sort_keys=True,ensure_ascii=False)
        now=now or datetime.now(IST)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row=db.execute('SELECT * FROM bookings WHERE request_token = ?',(request_token,)).fetchone()
            if row:
                ticket=self.unpack(row)
                if (row['flight_json']!=encoded or row['passengers']!=passengers or ticket['cabin']!=cabin or ticket['passenger_names']!=names or (seats is not None and ticket['seats']!=seats)):
                    raise ValueError('This confirmation was already used. Please select the flight again.')
                return ticket
            if departure_time(flight)<=now:raise ValueError('Choose a flight that departs in the future.')
            taken={r['seat'] for r in db.execute('SELECT seat FROM seat_holds WHERE flight_id = ? AND cabin = ?',(flight['id'],cabin))}
            available=[s for s in layout if s not in taken]
            selected=seats if seats is not None else available[:passengers]
            if len(selected)!=passengers or any(s in taken for s in selected):
                raise ValueError('Some seats were just booked. Please choose other seats or another class.')
            pricing=fare_quote(flight['price'],passengers,cabin)
            for _ in range(5):
                raw=secrets.token_hex(10).upper();reference='SKY-'+'-'.join(raw[i:i+4] for i in range(0,20,4))
                db.execute('SAVEPOINT reference_attempt')
                try:
                    db.execute('''INSERT INTO bookings
                        (reference,request_token,flight_json,passengers,total,status,created_at,cancelled_at,cabin,names_json,seats_json,pricing_json)
                        VALUES (?,?,?,?,?,'confirmed',?,NULL,?,?,?,?)''',
                        (reference,request_token,encoded,passengers,pricing['total_paise']/100,now.isoformat(),cabin,json.dumps(names),json.dumps(selected),json.dumps(pricing)))
                except self.integrity_error:
                    db.execute('ROLLBACK TO SAVEPOINT reference_attempt')
                    db.execute('RELEASE SAVEPOINT reference_attempt')
                    continue
                db.execute('RELEASE SAVEPOINT reference_attempt')
                db.executemany('INSERT INTO seat_holds VALUES (?,?,?,?)',[(flight['id'],cabin,s,reference) for s in selected])
                return self.unpack(db.execute('SELECT * FROM bookings WHERE reference = ?',(reference,)).fetchone())
            raise RuntimeError('A demo reference could not be created. Please try again.')

    def cancel(self,reference,now=None):
        reference=normalize_reference(reference)
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            changed=db.execute("UPDATE bookings SET status = 'cancelled', cancelled_at = ? WHERE reference = ? AND status = 'confirmed'",((now or datetime.now(IST)).isoformat(),reference)).rowcount==1
            if changed:db.execute('DELETE FROM seat_holds WHERE reference = ?',(reference,))
            ticket=self.unpack(db.execute('SELECT * FROM bookings WHERE reference = ?',(reference,)).fetchone())
            return ticket,changed
