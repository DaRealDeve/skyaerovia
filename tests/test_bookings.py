import concurrent.futures
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from bookings import BookingStore, IST, normalize_reference, ticket_text

NOW = datetime(2026,10,12,10,tzinfo=IST)
FLIGHT = {'id':'F1','airline':'Demo Air','from':'Delhi','to':'Mumbai','date':'2026-10-13',
          'departure':'12:00','arrival':'14:00','price':3900,'duration':120,'stops':0}

class TestBookings(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'tickets.sqlite3'
        self.store=BookingStore(self.path)
    def tearDown(self):self.tmp.cleanup()
    def create(self,token='a'*32,quantity=1):return self.store.create(FLIGHT,quantity,token,NOW)
    def test_reference_total_snapshot_and_reopen(self):
        flight=dict(FLIGHT); ticket=self.store.create(flight,2,'a'*32,NOW)
        self.assertRegex(ticket['reference'],r'^SKY-(?:[A-F0-9]{4}-){4}[A-F0-9]{4}$')
        self.assertEqual(ticket['total'],7800)
        flight['price']=1
        self.assertEqual(BookingStore(self.path).get(ticket['reference'])['flight']['price'],3900)
        self.assertEqual(normalize_reference(ticket['reference'].lower().replace('-',' ')),ticket['reference'])
    def test_repeated_and_concurrent_confirmation_produces_one_ticket(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            tickets=list(pool.map(lambda _:self.create(),range(8)))
        self.assertEqual(len({t['reference'] for t in tickets}),1)
        with self.store.connect() as db:self.assertEqual(db.execute('SELECT count(*) FROM bookings').fetchone()[0],1)
    def test_two_bookings_are_distinct(self):
        self.assertNotEqual(self.create()['reference'],self.create('b'*32)['reference'])
    def test_collision_retries_without_overwriting(self):
        with patch('bookings.secrets.token_hex',side_effect=['a'*20,'a'*20,'b'*20]):
            one=self.create(); two=self.create('b'*32)
        self.assertNotEqual(one['reference'],two['reference'])
        self.assertEqual(self.store.get(one['reference'])['status'],'confirmed')
    def test_cancel_is_idempotent_and_keeps_other_booking(self):
        one=self.create(); two=self.create('b'*32)
        cancelled,changed=self.store.cancel(one['reference'],NOW)
        self.assertTrue(changed); self.assertEqual(cancelled['status'],'cancelled')
        again,changed=self.store.cancel(one['reference'],NOW+timedelta(seconds=5))
        self.assertFalse(changed); self.assertEqual(again['cancelled_at'],cancelled['cancelled_at'])
        self.assertEqual(self.store.get(two['reference'])['status'],'confirmed')
    def test_unknown_or_invalid_reference_does_not_change_records(self):
        one=self.create()
        self.assertEqual(self.store.cancel('SKY-0000-0000-0000-0000-0000'),(None,False))
        for value in ('','TKT6590',"' OR 1=1 --",123):
            with self.assertRaises(ValueError):self.store.cancel(value)
        self.assertEqual(self.store.get(one['reference'])['status'],'confirmed')
    def test_invalid_quantity_token_price_and_past_departure(self):
        for value in (0,7,True,1.5,'2'):
            with self.assertRaises(ValueError):self.create(quantity=value)
        with self.assertRaises(ValueError):self.create(token='bad')
        for price in (0,-1,True,2.5):
            with self.assertRaises(ValueError):self.store.create({**FLIGHT,'price':price},1,'a'*32,NOW)
        with self.assertRaises(ValueError):self.store.create(FLIGHT,1,'a'*32,NOW+timedelta(days=2))
    def test_same_confirmation_cannot_change_passenger_count(self):
        self.create()
        with self.assertRaises(ValueError):self.create(quantity=2)
    def test_download_contains_actual_reference_and_current_status(self):
        one=self.create(); cancelled,_=self.store.cancel(one['reference'],NOW)
        text=ticket_text(cancelled)
        self.assertIn(one['reference'],text); self.assertIn('CANCELLED',text)
        self.assertIn('Not valid for travel',text); self.assertNotIn('password',text.lower())
