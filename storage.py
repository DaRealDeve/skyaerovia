"""External PostgreSQL for durable tickets; explicit SQLite fallback for local demos."""
import os
from contextlib import contextmanager
import streamlit as st
import psycopg
from psycopg.rows import dict_row
from bookings import BookingStore


class StorageError(Exception):
    pass


def database_url():
    value=os.getenv('DATABASE_URL','')
    if not value:
        try:value=st.secrets.get('DATABASE_URL','')
        except st.errors.StreamlitSecretNotFoundError:pass
    return value.strip() if isinstance(value,str) else ''


class PgSession:
    def __init__(self,db):self.db=db
    def execute(self,sql,args=()):
        if sql=='BEGIN IMMEDIATE':
            # Transaction lock serialises brief booking/cancellation writes across app instances.
            return self.db.execute('SELECT pg_advisory_xact_lock(742193012)')
        return self.db.execute(sql.replace('?','%s'),args)
    def executemany(self,sql,rows):
        return self.db.cursor().executemany(sql.replace('?','%s'),rows)


class PostgresBookingStore(BookingStore):
    integrity_error=psycopg.IntegrityError
    def __init__(self,url):
        if not url.startswith(('postgresql://','postgres://')):raise StorageError('Invalid database configuration.')
        self.url=url
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            db.execute('''CREATE TABLE IF NOT EXISTS bookings (
                reference TEXT PRIMARY KEY,request_token TEXT NOT NULL UNIQUE,
                flight_json TEXT NOT NULL,passengers INTEGER NOT NULL CHECK(passengers BETWEEN 1 AND 6),
                total NUMERIC NOT NULL CHECK(total>0),status TEXT NOT NULL CHECK(status IN ('confirmed','cancelled')),
                created_at TEXT NOT NULL,cancelled_at TEXT,cabin TEXT NOT NULL DEFAULT 'Economy',
                names_json TEXT,seats_json TEXT,pricing_json TEXT,owner_user_id TEXT)''')
            db.execute('''CREATE TABLE IF NOT EXISTS seat_holds (
                flight_id TEXT NOT NULL,cabin TEXT NOT NULL,seat TEXT NOT NULL,reference TEXT NOT NULL,
                PRIMARY KEY(flight_id,cabin,seat),FOREIGN KEY(reference) REFERENCES bookings(reference))''')

    @contextmanager
    def connect(self):
        try:
            with psycopg.connect(self.url,row_factory=dict_row,connect_timeout=10,
                                  sslmode='require') as db:
                db.execute("SET LOCAL statement_timeout = '15s'")
                yield PgSession(db)
        except psycopg.Error:
            # Database diagnostics can contain passwords/hosts: never expose them in the UI.
            raise StorageError('Ticket storage is temporarily unavailable. Please try again shortly.') from None


@st.cache_resource(show_spinner=False)
def persistent_store(url):return PostgresBookingStore(url)


def booking_store(root):
    url=database_url()
    return persistent_store(url) if url else BookingStore(root/'.data/bookings.sqlite3')


def storage_notice():
    if database_url():return 'Demo reservations only. Tickets are saved to your account and appear on any device after login. Save your PDF too.'
    return 'Demo reservations only. Database connection is not configured; these temporary tickets may reset on restart. Save your PDF.'
