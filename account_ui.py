"""Neon managed accounts in Skye's chat; no local password database."""
import os
import re
import time
from urllib.parse import urlparse
import jwt
import requests
import streamlit as st
import streamlit.components.v2 as components

# Public service address; this is not a credential.
AUTH_URL='https://ep-sweet-poetry-b39a7j74.neonauth.c-4.ap-southeast-1.aws.neon.tech/skyaerovia/auth'
ORIGIN='https://skyaerovia.streamlit.app'
BRIDGE_JS='''
export default function({data,setStateValue}) {
 const key='skyaerovia-account:'+data.url;
 try {
   if(data.clear) {sessionStorage.removeItem(key);return;}
   if(data.token) {sessionStorage.setItem(key,data.token);return;}
   const saved=sessionStorage.getItem(key);
   if(saved) setStateValue('restored',{token:saved,event:Date.now()});
 } catch { /* Login still works if browser session storage is unavailable. */ }
}
'''

@st.cache_data(ttl=300,show_spinner=False)
def public_keys(url):
    r=requests.get(url+'/.well-known/jwks.json',timeout=10)
    r.raise_for_status()
    return r.json()['keys']

def verify_identity(token,url):
    if not isinstance(token,str) or len(token)>12000:return None
    try:
        header=jwt.get_unverified_header(token)
        if header.get('alg')!='EdDSA':return None
        jwk=next(k for k in public_keys(url) if k.get('kid')==header.get('kid'))
        key=jwt.PyJWK.from_dict(jwk).key
        parsed=urlparse(url);origin=f'{parsed.scheme}://{parsed.netloc}'
        claims=jwt.decode(token,key,algorithms=['EdDSA'],issuer=origin,audience=origin,
                         options={'require':['exp','iat','sub','iss','aud']})
        if not isinstance(claims.get('sub'),str) or not claims['sub'] or claims.get('banned'):return None
        email=claims.get('email');name=claims.get('name')
        if not isinstance(email,str) or not email:return None
        return {'id':claims['sub'],'email':email[:254],'name':name[:60] if isinstance(name,str) else email[:60],'expires':claims['exp']}
    except (jwt.PyJWTError,requests.RequestException,StopIteration,ValueError,TypeError,KeyError):return None

class AccountError(Exception):pass

class ManagedAccounts:
    """HTTPS calls to the provider's documented OpenAPI; cookies stay server-side."""
    def __init__(self,url):
        self.url=url.rstrip('/')
        self.http=requests.Session()
        self.http.headers.update({'Origin':ORIGIN,'Accept':'application/json'})
    def call(self,path,payload=None):
        try:
            r=self.http.request('POST' if payload is not None else 'GET',self.url+path,json=payload,timeout=(5,20),allow_redirects=False)
            if r.status_code==429:raise AccountError('Too many attempts. Please wait a minute and try again.')
            if not r.ok:
                if path=='/sign-in/email':raise AccountError('Could not log in. Check your email and password, then try again.')
                if path=='/sign-up/email':raise AccountError('Could not register this email. If you already have an account, choose Log in.')
                raise AccountError('Account service is temporarily unavailable. Please try again.')
            return r.json()
        except (requests.RequestException,ValueError):
            raise AccountError('Account service is temporarily unavailable. Please try again.') from None
    def authenticate(self,mode,email,password,name=''):
        body={'email':email,'password':password}
        if mode=='register':body['name']=name
        self.call('/sign-up/email' if mode=='register' else '/sign-in/email',body)
        token=self.call('/token').get('token')
        user=verify_identity(token,self.url)
        if not user:raise AccountError('We could not verify this login. Please log in again.')
        return token,user
    def refresh(self):
        session=self.call('/get-session')
        if not isinstance(session,dict) or not session.get('user'):return None,None
        token=self.call('/token').get('token')
        return token,verify_identity(token,self.url)
    def sign_out(self):
        try:self.call('/sign-out',{})
        finally:self.http.cookies.clear();self.http.close()

def go_account(mode):
    st.session_state.view=mode
    st.session_state.account_notice=None
    st.session_state.account_error=None

def log_out():
    gateway=st.session_state.pop('account_gateway',None)
    if gateway:
        try:gateway.sign_out()
        except AccountError:pass
    st.session_state.account_user=None
    st.session_state.account_token=None
    st.session_state.account_clear=True
    st.session_state.account_notice='You are logged out.'
    st.session_state.view='search'

def validate_registration(name,email,password,confirm):
    if not name or len(name)>60:return 'Enter your name, up to 60 characters.'
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',email) or len(email)>254:return 'Enter a valid email address.'
    if not 8<=len(password)<=128:return 'Use a password of 8–128 characters.'
    if password!=confirm:return 'The two passwords do not match. Please enter them again.'
    return None

def submit_account(mode):
    """Callbacks erase password widget values before the next script render."""
    prefix='register' if mode=='register' else 'login'
    email=st.session_state.get(prefix+'_email','').strip().lower()
    password=st.session_state.pop(prefix+'_password','')
    confirm=st.session_state.pop('register_confirm','') if mode=='register' else ''
    name=st.session_state.get('register_name','').strip() if mode=='register' else ''
    st.session_state[prefix+'_password']=''
    if mode=='register':st.session_state.register_confirm=''
    error=validate_registration(name,email,password,confirm) if mode=='register' else (
        'Enter your email and password.' if not email or not password else None)
    if error:st.session_state.account_error=error;return
    url=os.getenv('NEON_AUTH_BASE_URL',AUTH_URL).rstrip('/')
    gateway=ManagedAccounts(url)
    try:
        token,user=gateway.authenticate(mode,email,password,name)
    except AccountError as e:
        gateway.http.close();st.session_state.account_error=str(e);return
    finally:password='';confirm=''
    st.session_state.account_gateway=gateway
    st.session_state.account_user=user
    st.session_state.account_token=token
    st.session_state.account_clear=False
    st.session_state.account_error=None
    st.session_state.account_notice='Your account is ready. You are now logged in.' if mode=='register' else 'You are now logged in.'
    st.session_state.view='search'

@st.fragment(run_every='5m')
def session_bridge(url):
    user=st.session_state.get('account_user')
    gateway=st.session_state.get('account_gateway')
    # A live app session can renew through the provider's server-side cookie.
    if gateway and user and user.get('expires',0)<time.time()+360:
        try:
            token,user=gateway.refresh()
            st.session_state.account_token=token
            st.session_state.account_user=user
        except AccountError:pass
    if user and user.get('expires',0)<=time.time():
        st.session_state.account_user=None;st.session_state.account_token=None
        st.session_state.account_clear=True
        st.session_state.account_notice='Your login has expired. Please log in again.'
        st.rerun()
    bridge=components.component('skye_account_session',js=BRIDGE_JS)
    result=bridge(data={'url':url,'token':st.session_state.get('account_token'),'clear':st.session_state.get('account_clear',False)},key='skye_account_session',on_restored_change=lambda:None)
    event=result.restored
    if isinstance(event,dict) and event.get('event')!=st.session_state.get('account_restore_event'):
        st.session_state.account_restore_event=event.get('event')
        if not st.session_state.get('account_clear') and not st.session_state.get('account_user'):
            token=event.get('token');user=verify_identity(token,url)
            if user:
                st.session_state.account_user=user;st.session_state.account_token=token
            else:st.session_state.account_clear=True
            st.rerun()

def render_accounts():
    url=os.getenv('NEON_AUTH_BASE_URL',AUTH_URL).rstrip('/')
    session_bridge(url)
    user=st.session_state.get('account_user')
    if user:st.write(f"Welcome, {user['name']}! You’re logged in.")
    if st.session_state.get('account_notice'):st.info(st.session_state.account_notice)
    mode=st.session_state.view
    if mode in ('login','register') and not user:
        st.subheader('Create your SkyAerovia account' if mode=='register' else 'Log in to SkyAerovia')
        st.caption('Your password stays out of Skye’s messages. Use the secure fields below.')
        with st.form('account_'+mode):
            if mode=='register':st.text_input('Your name',max_chars=60,key='register_name')
            st.text_input('Email',max_chars=254,key=mode+'_email')
            st.text_input('Password',type='password',max_chars=128,key=mode+'_password',help='Use 8–128 characters.')
            if mode=='register':st.text_input('Confirm password',type='password',max_chars=128,key='register_confirm')
            st.form_submit_button('Create account' if mode=='register' else 'Log in',type='primary',on_click=submit_account,args=(mode,))
        if st.session_state.get('account_error'):st.error(st.session_state.account_error)
    return user

def account_intent(prompt):
    if re.match(r'^\s*(?:log\s*in|login|sign\s*in)\b',prompt,re.I):return 'login'
    if re.match(r'^\s*(?:register|sign\s*up|signup|create\s+(?:an?\s+)?account)\b',prompt,re.I):return 'register'
    return None
