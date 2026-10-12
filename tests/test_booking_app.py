import json
from datetime import datetime, timedelta
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
from zoneinfo import ZoneInfo
import extractor
from bookings import BookingStore
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class BookingAppFixture:
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name)
        shutil.copyfile(ROOT/'app.py',self.root/'app.py')
        day=(datetime.now(ZoneInfo('Asia/Kolkata')).date()+timedelta(days=1)).isoformat()
        base={'airline':'Demo Air','from':'Delhi','to':'Mumbai','date':day,'departure':'12:00',
              'arrival':'14:00','price':3900,'duration':120,'stops':0}
        (self.root/'flights.json').write_text(json.dumps([{**base,'id':'F1'},{**base,'id':'F2','price':4200}]))
        self.mock=patch.object(extractor,'extract_with_ai',side_effect=RuntimeError('offline UI test')); self.mock.start()
        self.app=AppTest.from_file(str(self.root/'app.py'),default_timeout=10).run()
    def tearDown(self):self.mock.stop(); self.tmp.cleanup()
    def button(self,label):return next(b for b in self.app.button if b.label==label)
    def click(self,label):self.button(label).click().run(); self.assertEqual(len(self.app.exception),0)
    def book(self,quantity=1):
        self.app.chat_input[0].set_value('Delhi to Mumbai tomorrow').run()
        self.app.button(key='book_F1').click().run()
        self.app.number_input(key='passenger_count').set_value(quantity).run()
        self.click('Confirm demo booking')
        return self.app.session_state['last_ticket']
    def store(self):return BookingStore(self.root/'.data/bookings.sqlite3')
class TestBookingApp(BookingAppFixture, unittest.TestCase):
    def test_confirmation_yes_and_no_flow(self):
        first=self.book(2); self.assertEqual(self.store().get(first)['total'],8190)
        self.click('Yes, book another ticket'); self.assertEqual(self.app.session_state['view'],'search')
        self.app.button(key='book_F2').click().run(); self.click('Confirm demo booking')
        second=self.app.session_state['last_ticket']; self.assertNotEqual(first,second)
        self.click('No, I’m done'); self.assertEqual(self.app.session_state['view'],'tickets')
        self.assertEqual(len(self.app.session_state['booking_refs']),2)
    def test_cancel_only_after_confirmation_keep_then_cancel(self):
        ref=self.book(); self.click('Cancel a ticket')
        self.app.text_input[0].set_value(ref.lower()).run(); self.click('Find ticket')
        self.click('Cancel this demo booking'); self.click('Keep my booking')
        self.assertEqual(self.store().get(ref)['status'],'confirmed')
        self.click('Cancel this demo booking'); self.click('Yes, cancel booking')
        self.assertEqual(self.store().get(ref)['status'],'cancelled')
        self.assertTrue(self.app.success)
        self.assertFalse(any(b.label=='Yes, cancel booking' for b in self.app.button))
    def test_changed_reference_clears_pending_cancellation(self):
        ref=self.book(); self.click('Cancel a ticket')
        self.app.text_input[0].set_value(ref).run(); self.click('Find ticket'); self.click('Cancel this demo booking')
        self.app.text_input[0].set_value('invalid').run()
        self.assertFalse(any(b.label=='Yes, cancel booking' for b in self.app.button))
        self.assertEqual(self.store().get(ref)['status'],'confirmed')
    def test_clear_chat_preserves_tickets(self):
        ref=self.book(); self.click('Clear chat')
        self.assertEqual(self.app.session_state['view'],'search')
        self.assertIn(ref,self.app.session_state['booking_refs'])
        self.assertEqual(self.store().get(ref)['status'],'confirmed')
        self.assertIsNone(self.app.session_state['results'])
    def test_invalid_and_unknown_reference_are_useful(self):
        self.click('Cancel a ticket'); self.click('Find ticket'); self.assertTrue(self.app.warning)
        self.app.text_input[0].set_value('SKY-0000-0000-0000-0000-0000').run()
        self.click('Find ticket'); self.assertIn('No demo ticket',self.app.warning[0].value)
    def test_saved_reference_works_after_new_session(self):
        ref=self.book()
        self.app=AppTest.from_file(str(self.root/'app.py'),default_timeout=10).run()
        self.assertEqual(self.app.session_state['booking_refs'],[])
        self.click('Cancel a ticket'); self.app.text_input[0].set_value(ref).run(); self.click('Find ticket')
        self.assertTrue(any(ref in c.value for c in self.app.code))
    def test_cancellation_chat_opens_guided_flow(self):
        self.app.chat_input[0].set_value('cancel my ticket').run()
        self.assertEqual(len(self.app.exception),0)
        self.assertEqual(self.app.session_state['view'],'cancel')
        self.assertTrue(self.app.text_input)
