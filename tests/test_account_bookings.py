import json,secrets,sqlite3,tempfile,unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from bookings import BookingStore

class TestAccountBookings(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/'tickets.db';self.addCleanup(self.tmp.cleanup)
        self.store=BookingStore(self.path);self.a=self.store.for_account('user-a');self.b=self.store.for_account('user-b')
        self.flight={'id':'OWNED-FLIGHT','airline':'Demo Air','from':'Delhi','to':'Goa','date':(datetime.now(ZoneInfo('Asia/Kolkata')).date()+timedelta(days=10)).isoformat(),'departure':'12:00','arrival':'14:00','duration':120,'stops':0,'price':4000}
    def book(self,account=None,token=None):return (account or self.a).create(self.flight,1,token or secrets.token_hex(16))
    def test_new_device_history_and_frozen_snapshot(self):
        ticket=self.book();new=BookingStore(self.path).for_account('user-a');rows,more=new.history()
        self.assertEqual([r['reference'] for r in rows],[ticket['reference']]);self.assertFalse(more)
        self.assertEqual(rows[0]['pricing'],ticket['pricing']);self.assertEqual(rows[0]['seats'],ticket['seats'])
    def test_other_user_cannot_list_get_or_cancel_ticket(self):
        ticket=self.book();ref=ticket['reference'];self.assertEqual(self.b.history(),([],False));self.assertIsNone(self.b.get(ref))
        self.assertEqual(self.b.cancel(ref),(None,False));self.assertEqual(self.a.get(ref)['status'],'confirmed')
        self.assertNotIn(ticket['seats'][0],self.store.available_seats(self.flight['id'],'Economy'))
    def test_cancelled_tickets_remain_in_own_history(self):
        ticket=self.book();self.a.cancel(ticket['reference']);rows,_=self.a.history()
        self.assertEqual(rows[0]['status'],'cancelled');self.assertEqual(rows[0]['pricing'],ticket['pricing'])
        self.assertIn(ticket['seats'][0],self.store.available_seats(self.flight['id'],'Economy'))
    def test_legacy_is_hidden_until_explicit_claim(self):
        old=self.store.create(self.flight,1,secrets.token_hex(16));ref=old['reference']
        self.assertEqual(self.a.history(),([],False));self.assertIsNone(self.a.get(ref))
        claimed=self.a.claim_older(ref);self.assertEqual(claimed['owner_user_id'],'user-a');self.assertEqual(claimed['pricing'],old['pricing'])
        self.assertEqual(self.a.claim_older(ref)['reference'],ref);self.assertIsNone(self.b.claim_older(ref));self.assertIsNone(self.b.get(ref))
    def test_legacy_concurrent_claim_has_one_winner(self):
        old=self.store.create(self.flight,1,secrets.token_hex(16))
        with ThreadPoolExecutor(2) as pool:results=list(pool.map(lambda account:account.claim_older(old['reference']),[self.a,self.b]))
        self.assertEqual(sum(r is not None for r in results),1)
        self.assertIn(self.store.get(old['reference'])['owner_user_id'],['user-a','user-b'])
    def test_history_pages_do_not_repeat_or_mix_users(self):
        expected={self.book()['reference'] for _ in range(25)};self.book(self.b)
        first,more=self.a.history();second,more2=self.a.history(1)
        self.assertEqual((len(first),more,len(second),more2),(20,True,5,False))
        self.assertEqual({r['reference'] for r in first+second},expected)
        self.assertTrue(all(r['owner_user_id']=='user-a' for r in first+second))
    def test_idempotency_token_cannot_be_replayed_by_other_owner(self):
        token=secrets.token_hex(16);ticket=self.book(token=token)
        self.assertEqual(self.book(token=token)['reference'],ticket['reference'])
        with self.assertRaises(ValueError):self.book(self.b,token)
    def test_owner_input_cannot_be_overridden_or_injected(self):
        for owner in [None,'',"user-a' OR 1=1",{},'x'*129]:
            with self.assertRaises(ValueError):self.store.for_account(owner)
        with self.assertRaises(ValueError):self.a.create(self.flight,1,secrets.token_hex(16),owner_user_id='user-b')
    def test_local_old_schema_upgrades_without_assigning_owners(self):
        other=Path(self.tmp.name)/'older.db'
        with sqlite3.connect(other) as db:db.execute('''CREATE TABLE bookings(reference TEXT PRIMARY KEY,request_token TEXT NOT NULL UNIQUE,flight_json TEXT NOT NULL,passengers INTEGER NOT NULL,total NUMERIC NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,cancelled_at TEXT)''')
        migrated=BookingStore(other)
        with migrated.connect() as db:self.assertIn('owner_user_id',[r['name'] for r in db.execute('PRAGMA table_info(bookings)')])

from streamlit.testing.v1 import AppTest
from test_booking_app import BookingAppFixture
class TestAccountHistoryUI(BookingAppFixture,unittest.TestCase):
    def test_new_browser_session_lists_account_history_without_reference_input(self):
        ref=self.book()
        self.app=AppTest.from_file(str(self.root/'app.py'),default_timeout=25).run()
        self.assertEqual(self.app.session_state['booking_refs'],[])
        self.sign_in_test_session();self.click('My demo tickets')
        self.assertTrue(any(ref in c.value for c in self.app.code))
    def test_second_account_cannot_download_or_cancel_first_accounts_ticket(self):
        ref=self.book()
        self.app.session_state['account_user']['id']='other-user'
        self.app.session_state['view']='tickets';self.app.run()
        self.assertFalse(self.app.code)
        self.click('Cancel a ticket');self.app.text_input(key='cancel_reference').set_value(ref).run();self.click('Find ticket')
        self.assertFalse(self.app.code)
        self.assertFalse(any(b.label=='Cancel this demo booking' for b in self.app.button))
        self.assertEqual(self.store().get(ref)['status'],'confirmed')
    def test_older_ticket_claim_then_automatic_history(self):
        import secrets
        ref=self.store().create({'id':'LEGACY','airline':'Demo Air','from':'Delhi','to':'Mumbai','date':self.app.session_state.get('request',{}).get('date') or (datetime.now(ZoneInfo('Asia/Kolkata')).date()+timedelta(days=10)).isoformat(),'departure':'12:00','arrival':'14:00','duration':120,'stops':0,'price':4000},1,secrets.token_hex(16))['reference']
        self.click('My demo tickets');self.assertFalse(self.app.code)
        self.app.text_input(key='older_ticket_reference').set_value(ref)
        self.click('Add to my account')
        self.assertTrue(any(ref in c.value for c in self.app.code))
        self.assertEqual(self.store().get(ref)['owner_user_id'],'test-user')
