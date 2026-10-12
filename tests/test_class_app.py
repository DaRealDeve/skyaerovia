from test_booking_app import BookingAppFixture
import unittest
from pypdf import PdfReader
from io import BytesIO
from ticket_pdf import ticket_pdf

class TestClassApp(BookingAppFixture, unittest.TestCase):
    def test_cabin_change_updates_quote_and_selected_seats(self):
        self.app.chat_input[0].set_value('Delhi to Mumbai tomorrow').run()
        self.app.button(key='book_F1').click().run()
        self.app.radio(key='travel_class').set_value('Business').run()
        name=next(t for t in self.app.text_input if t.label=='Passenger 1 name (English)');name.set_value('Demo Traveller').run()
        self.click('Confirm demo booking');ref=self.app.session_state['last_ticket'];ticket=self.store().get(ref)
        self.assertEqual(ticket['cabin'],'Business');self.assertEqual(ticket['total'],10124.4)
        self.assertEqual(ticket['passenger_names'],['Demo Traveller']);self.assertEqual(ticket['seats'],['1A'])
        self.assertIn('GST (18%)',PdfReader(BytesIO(ticket_pdf(ticket))).pages[0].extract_text())
    def test_quick_actions_below_greeting_inside_assistant_message(self):
        assistant=self.app.chat_message[0]
        self.assertTrue(any('Namaste!' in m.value for m in assistant.markdown))
        labels=[b.label for b in assistant.button]
        self.assertEqual(labels,['Log in','Register','Find flights','My demo tickets','Cancel a ticket'])
    def test_invalid_name_blocks_creation_gracefully(self):
        self.app.chat_input[0].set_value('Delhi to Mumbai tomorrow').run();self.app.button(key='book_F1').click().run()
        self.app.text_input[0].set_value('<script>').run();self.click('Confirm demo booking')
        self.assertTrue(self.app.error);self.assertIsNone(self.app.session_state['last_ticket'])
