from pathlib import Path
import gzip,json,shutil,tempfile,unittest
from datetime import datetime,timedelta
from zoneinfo import ZoneInfo
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import extractor
from schedule import build_catalog
from storage import PostgresBookingStore,StorageError
import psycopg
ROOT=Path(__file__).resolve().parents[1]
class TestExpandedApp(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        shutil.copyfile(ROOT/'app.py',self.root/'app.py')
        (self.root/'flight_catalog.json.gz').write_bytes(gzip.compress(json.dumps(build_catalog()).encode()))
        self.mock=patch.object(extractor,'extract_with_ai',side_effect=RuntimeError('offline'));self.mock.start()
        self.app=AppTest.from_file(str(self.root/'app.py'),default_timeout=15).run()
    def tearDown(self):self.mock.stop();self.tmp.cleanup()
    def cards(self):return [m for m in self.app.markdown if '<div class="flight-card">' in m.value]
    def test_search_form_new_route_has_six_results(self):
        self.app.selectbox(key='form_origin').select('Madurai')
        self.app.selectbox(key='form_destination').select('Raipur')
        next(b for b in self.app.button if b.label=='Search flights').click().run()
        self.assertFalse(self.app.exception);self.assertEqual(len(self.cards()),6)
        self.assertEqual(self.app.session_state['results']['origin'],'Madurai')
    def test_chat_overnight_cards_and_cabin_preference(self):
        self.app.chat_input[0].set_value('Delhi to Kochi tomorrow').run()
        self.assertEqual(len(self.cards()),6);self.assertTrue(any('+1 day' in m.value for m in self.cards()))
        self.app.selectbox(key='preferred_cabin').select('Business').run()
        self.assertTrue(all('Business' in m.value for m in self.cards()))
        next(b for b in self.app.button if b.label=='Book demo ticket').click().run()
        self.assertEqual(self.app.radio(key='travel_class').value,'Business')
    def test_filters_and_relax_button(self):
        self.app.chat_input[0].set_value('Delhi to Jaipur tomorrow under 10').run()
        self.assertFalse(self.cards());self.assertTrue(any('lowest base fare' in i.value for i in self.app.info))
        next(b for b in self.app.button if b.label=='Show all flights on this route').click().run()
        self.assertEqual(len(self.cards()),6)
        self.app.multiselect(key='airline_choices').set_value(['IndiGo']).run()
        self.assertEqual(len(self.cards()),1)
        self.app.multiselect(key='airline_choices').set_value([]).run()
        self.app.selectbox(key='time_choice').select('Morning (05–12)').run()
        self.assertEqual(len(self.cards()),3)
    def test_out_of_window_has_clear_date_range(self):
        later=(datetime.now(ZoneInfo('Asia/Kolkata')).date()+timedelta(days=100)).isoformat()
        self.app.chat_input[0].set_value('Delhi to Goa on '+later).run()
        self.assertTrue(any('outside our schedule' in m.value for m in self.app.markdown))
        self.assertFalse(self.cards())
class TestSafeStorage(unittest.TestCase):
    def test_db_errors_are_sanitized(self):
        with patch('storage.psycopg.connect',side_effect=psycopg.OperationalError('private-password-and-host')):
            with self.assertRaises(StorageError) as cm:PostgresBookingStore('postgresql://example.invalid/db')
        self.assertNotIn('private-password',str(cm.exception))
    def test_invalid_url_rejected(self):
        with self.assertRaises(StorageError):PostgresBookingStore('https://example.invalid')
