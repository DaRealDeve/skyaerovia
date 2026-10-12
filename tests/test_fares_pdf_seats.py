from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from pypdf import PdfReader
from bookings import BookingStore, IST
from fares import fare_quote, cabin_seats, seat_label
from ticket_pdf import ticket_pdf

NOW=datetime(2026,10,12,10,tzinfo=IST)
FLIGHT={'id':'DEMO','airline':'Demo Air','from':'Delhi','to':'Mumbai','date':'2026-10-13','departure':'12:00','arrival':'14:00','price':3900,'duration':120,'stops':0}

class TestFareQuotes(unittest.TestCase):
    def test_three_cabin_rates_and_totals(self):
        for cabin,subtotal,gst,total in [('Economy',390000,19500,409500),('Premium Economy',565500,101790,667290),('Business',858000,154440,1012440)]:
            with self.subTest(cabin=cabin):
                q=fare_quote(3900,1,cabin)
                self.assertEqual((q['subtotal_paise'],q['gst_paise'],q['total_paise']),(subtotal,gst,total))
                self.assertEqual(q['other_fees_paise'],0)
    def test_multiplication_and_paise_rounding(self):
        q=fare_quote(3900,2,'Economy');self.assertEqual(q['total_paise'],819000)
        q=fare_quote(1,1,'Premium Economy');self.assertEqual(q['subtotal_paise'],145);self.assertEqual(q['gst_paise'],26);self.assertEqual(q['total_paise'],171)
    def test_invalid_classes_prices_and_quantity(self):
        for cabin,price,n in [('First',3900,1),('Economy',True,1),('Economy',3900,0),('Economy',3.1,1)]:
            with self.assertRaises(ValueError):fare_quote(price,n,cabin)
    def test_seat_layouts_and_labels(self):
        self.assertIn('12A',cabin_seats('Economy'));self.assertIn('6F',cabin_seats('Premium Economy'));self.assertIn('1C',cabin_seats('Business'))
        self.assertNotIn('A1',cabin_seats('Economy'))
        self.assertEqual(seat_label('12A'),'12A · Window');self.assertEqual(seat_label('12C'),'12C · Aisle');self.assertEqual(seat_label('12B'),'12B · Middle')

class TestSeatsAndPdf(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'demo.sqlite3';self.store=BookingStore(self.path)
    def tearDown(self):self.tmp.cleanup()
    def create(self,token='a'*32,**kwargs):return self.store.create(FLIGHT,1,token,NOW,**kwargs)
    def test_requested_seat_reserves_and_cancellation_releases_it(self):
        one=self.create(cabin='Business',seats=['1F'],passenger_names=['Demo Traveller'])
        self.assertNotIn('1F',self.store.available_seats('DEMO','Business'))
        with self.assertRaises(ValueError):self.create('b'*32,cabin='Business',seats=['1F'])
        self.store.cancel(one['reference'],NOW)
        self.assertIn('1F',self.store.available_seats('DEMO','Business'))
        self.assertEqual(self.create('c'*32,cabin='Business',seats=['1F'])['seats'],['1F'])
    def test_concurrent_competing_requests_do_not_double_book_seat(self):
        def reserve(token):
            try:return self.create(token,seats=['12A'])
            except ValueError:return None
        with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(reserve,['a'*32,'b'*32]))
        self.assertEqual(sum(r is not None for r in results),1)
        with self.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM bookings').fetchone()[0],1)
    def test_separate_cabins_and_flights_have_independent_inventory(self):
        self.create(seats=['12A']);self.create('b'*32,cabin='Business',seats=['1A'])
        other={**FLIGHT,'id':'OTHER'};self.assertEqual(self.store.create(other,1,'c'*32,NOW,seats=['12A'])['seats'],['12A'])
    def test_bad_and_duplicate_seats_names_are_rejected(self):
        for seats in (['A1'],['1A'],[[]]):
            with self.assertRaises(ValueError):self.create(seats=seats)
        with self.assertRaises(ValueError):self.store.create(FLIGHT,2,'a'*32,NOW,seats=['12A','12A'])
        for names in ([],[''],['<script>'],['x'*61]):
            with self.assertRaises(ValueError):self.create(passenger_names=names)
    def test_duplicate_confirmation_preserves_pricing_and_seat_snapshot(self):
        one=self.create(seats=['12A'],passenger_names=["O'Neil"])
        with patch('bookings.fare_quote',side_effect=RuntimeError('pricing changed')):
            again=self.create(seats=['12A'],passenger_names=["O'Neil"])
        self.assertEqual(again['pricing'],one['pricing']);self.assertEqual(again['seats'],one['seats'])
        with self.assertRaises(ValueError):self.create(seats=['12B'],passenger_names=["O'Neil"])
    def test_pdf_reference_class_names_seat_tax_and_total(self):
        one=self.create(cabin='Business',seats=['1F'],passenger_names=['Demo Traveller'])
        data=ticket_pdf(one);self.assertTrue(data.startswith(b'%PDF-'))
        reader=PdfReader(BytesIO(data));self.assertEqual(len(reader.pages),1)
        text=reader.pages[0].extract_text()
        for value in [one['reference'],'DEMO FLIGHT TICKET','BUSINESS','Demo Traveller','1F','GST (18%)','INR 10,124.40','NOT VALID FOR TRAVEL']:
            self.assertIn(value,text)
        self.assertEqual(tuple(round(float(v)) for v in reader.pages[0].mediabox[2:]),(842,595))
    def test_cancelled_pdf_changes_status_without_changing_fare(self):
        one=self.create();cancelled,_=self.store.cancel(one['reference'],NOW)
        text=PdfReader(BytesIO(ticket_pdf(cancelled))).pages[0].extract_text()
        self.assertIn('CANCELLED',text);self.assertIn('INR 4,095.00',text)
        self.assertEqual(cancelled['pricing'],one['pricing'])
    def test_legacy_database_migration_retains_original_fare_and_reference(self):
        path=Path(self.tmp.name)/'legacy.sqlite3';ref='SKY-AAAA-AAAA-AAAA-AAAA-AAAA'
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE bookings(reference TEXT PRIMARY KEY,request_token TEXT UNIQUE,flight_json TEXT,passengers INTEGER,total INTEGER,status TEXT,created_at TEXT,cancelled_at TEXT)')
            db.execute('INSERT INTO bookings VALUES(?,?,?,?,?,?,?,NULL)',(ref,'a'*32,json.dumps(FLIGHT),1,3900,'confirmed',NOW.isoformat()))
        store=BookingStore(path);ticket=store.get(ref)
        self.assertEqual(ticket['total'],3900);self.assertEqual(ticket['pricing']['version'],1);self.assertEqual(ticket['seats'],[])
        text=PdfReader(BytesIO(ticket_pdf(ticket))).pages[0].extract_text();self.assertIn('INR 3,900.00',text);self.assertIn('GST not recorded',text)
        self.assertTrue(store.cancel(ref,NOW)[1])
