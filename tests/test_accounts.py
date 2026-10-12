import time,unittest
from types import SimpleNamespace
from unittest.mock import patch
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import jwt
from streamlit.testing.v1 import AppTest
from pathlib import Path
import account_ui
from test_booking_app import BookingAppFixture

class TestIdentityVerification(unittest.TestCase):
    def setUp(self):
        self.private=Ed25519PrivateKey.generate()
        self.jwk=jwt.PyJWK.from_dict({'kty':'OKP','crv':'Ed25519','x':jwt.utils.base64url_encode(self.private.public_key().public_bytes_raw()).decode(),'kid':'test-key'})
        self.claims={'sub':'test-user','name':'Demo Name','email':'demo@example.com','iat':int(time.time()),'exp':int(time.time())+900,'iss':'https://auth.example.com','aud':'https://auth.example.com'}
        self.keys=patch.object(account_ui,'public_keys',return_value=[self.jwk._jwk_data]);self.keys.start();self.addCleanup(self.keys.stop)
    def token(self,**updates):
        return jwt.encode({**self.claims,**updates},self.private,algorithm='EdDSA',headers={'kid':'test-key'})
    def test_signed_live_identity(self):
        self.assertEqual(account_ui.verify_identity(self.token(),'https://auth.example.com/demo/auth')['id'],'test-user')
    def test_expired_and_wrong_issuer_and_audience_denied(self):
        for updates in ({'exp':int(time.time())-20},{'iss':'https://other.example.com'},{'aud':'https://other.example.com'},{'banned':True}):
            self.assertIsNone(account_ui.verify_identity(self.token(**updates),'https://auth.example.com/demo/auth'))
    def test_forged_identity_and_unsigned_tokens_denied(self):
        forged=jwt.encode(self.claims,Ed25519PrivateKey.generate(),algorithm='EdDSA',headers={'kid':'test-key'})
        self.assertIsNone(account_ui.verify_identity(forged,'https://auth.example.com/demo/auth'))
        self.assertIsNone(account_ui.verify_identity(jwt.encode(self.claims,'test-only',algorithm='HS256'),'https://auth.example.com/demo/auth'))
    def test_invalid_shapes_and_unknown_key_denied(self):
        for token in (None,{},'not-a-token','x'*12001):self.assertIsNone(account_ui.verify_identity(token,'https://auth.example.com/demo/auth'))
        with patch.object(account_ui,'public_keys',return_value=[]):self.assertIsNone(account_ui.verify_identity(self.token(),'https://auth.example.com/demo/auth'))
    def test_service_failure_returns_no_identity(self):
        import requests
        with patch.object(account_ui,'public_keys',side_effect=requests.ConnectionError('private details')):
            self.assertIsNone(account_ui.verify_identity(self.token(),'https://auth.example.com/demo/auth'))

class TestChatAccounts(BookingAppFixture,unittest.TestCase):
    def logged_out(self):self.click('Log out')
    def test_first_screen_only_has_register_and_login(self):
        self.logged_out()
        self.assertEqual([b.label for b in self.app.button],['Register','Log in'])
        self.assertFalse(self.app.chat_input);self.assertFalse(self.app.selectbox)
        self.assertFalse(self.app.sidebar.button)
    def test_forms_never_reveal_flight_features(self):
        self.logged_out();self.click('Register')
        self.assertEqual([t.label for t in self.app.text_input],['Your name','Email','Password','Confirm password'])
        self.assertFalse(self.app.chat_input);self.assertFalse(self.app.selectbox)
        self.app.button(key='nav_login').click().run()
        self.assertEqual([t.label for t in self.app.text_input],['Email','Password'])
        self.assertFalse(self.app.chat_input)
    def test_authenticated_session_unlocks_every_requested_option(self):
        self.assertTrue(self.app.selectbox(key='form_origin'));self.assertTrue(self.app.chat_input)
        for label in ['Find flights','My demo tickets','Cancel a ticket']:self.assertTrue(self.button(label))
        self.assertFalse(any(b.label in ('Register','Log in') for b in self.app.button))
    def test_account_command_does_not_record_password(self):
        self.app.chat_input[0].set_value('login demo@example.com sample-password').run()
        self.assertNotIn('sample-password',str(self.app.session_state['messages']))
    def test_logout_clears_session_history_but_keeps_database_ticket(self):
        ref=self.book();self.logged_out()
        self.assertIsNone(self.app.session_state['account_user'])
        self.assertEqual(self.app.session_state['booking_refs'],[])
        self.assertEqual(self.store().get(ref)['status'],'confirmed')
        self.assertFalse(self.app.chat_input);self.assertFalse(self.app.selectbox)
    def test_expired_login_blocks_stale_ticket_view(self):
        self.app.session_state['account_user']['expires']=time.time()-20
        self.app.session_state['view']='cancel';self.app.run()
        self.assertEqual([b.label for b in self.app.button],['Register','Log in'])
        self.assertFalse(self.app.chat_input);self.assertFalse(self.app.text_input)
    def test_selected_route_without_login_cannot_bypass_gate(self):
        self.logged_out();self.app.session_state['view']='search'
        self.app.session_state['results']={'origin':'Delhi','destination':'Mumbai','date':'2026-11-25'}
        self.app.run()
        self.assertFalse(self.app.chat_input);self.assertFalse(self.app.selectbox)
        self.assertEqual([b.label for b in self.app.button],['Register','Log in'])
    def test_clear_chat_keeps_login(self):
        self.click('Clear chat');self.assertEqual(self.app.session_state['account_user']['id'],'test-user')

class TestRegistrationValidation(unittest.TestCase):
    def test_valid_and_invalid_registration_fields(self):
        self.assertIsNone(account_ui.validate_registration('Demo','demo@example.com','test-only-password','test-only-password'))
        for fields in [('', 'demo@example.com','test-only-password','test-only-password'),('Demo','broken','test-only-password','test-only-password'),('Demo','demo@example.com','short','short'),('Demo','demo@example.com','test-only-password','different')]:
            self.assertIsNotNone(account_ui.validate_registration(*fields))
    def test_auth_errors_never_show_provider_body(self):
        gateway=account_ui.ManagedAccounts('https://auth.example.com')
        response=SimpleNamespace(status_code=401,ok=False,text='private-password-or-token')
        with patch.object(gateway.http,'request',return_value=response):
            with self.assertRaises(account_ui.AccountError) as error:gateway.call('/sign-in/email',{'email':'demo@example.com','password':'test-only'})
            self.assertNotIn('private',str(error.exception))
        gateway.http.close()
