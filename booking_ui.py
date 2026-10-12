"""Guided guest demo booking and cancellation, written for SkyAerovia."""
import secrets
import sqlite3
import streamlit as st
from bookings import normalize_reference
from storage import booking_store, storage_notice, StorageError
from schedule import find_flight
from fares import CABINS, fare_quote, seat_label
from ticket_pdf import ticket_pdf


def navigate(view):
    st.session_state.view = view


def start_booking(flight_id, cabin="Economy"):
    st.session_state.update(selected_flight=flight_id, booking_token=secrets.token_hex(16),
                            last_ticket=None, passenger_count=1, travel_class=cabin, view='booking')


def another_ticket(yes):
    st.session_state.update(selected_flight=None, last_ticket=None, view='search' if yes else 'tickets')


def open_cancellation(reference=None):
    st.session_state.update(view='cancel', cancel_reference=reference or '', cancel_ticket=reference,
                            cancel_confirming=False, cancel_notice=None)


def set_cancel_confirmation(value):
    st.session_state.cancel_confirming = value


def summary(ticket):
    f = ticket['flight']
    st.markdown('**Your booking reference**')
    st.code(ticket['reference'], language=None)
    st.write(f'**{f["airline"]} · {f["from"]} → {f["to"]}**')
    st.write(f'{f["date"]} · {f["departure"]} — {f["arrival"]} IST')
    if f.get('arrival_date',f['date']) != f['date']:st.caption('Arrives '+f['arrival_date']+' (next day)')
    st.write(f'{ticket["passengers"]} passenger(s) · {ticket["cabin"]} · Demo total ₹{ticket["total"]:,.2f}')
    for i,name in enumerate(ticket['passenger_names']):
        seat = ticket['seats'][i] if i < len(ticket['seats']) else 'Not assigned'
        st.write(f'{name} · Seat {seat}')
    with st.expander('Fare and GST breakdown'):
        show_quote(ticket['pricing'])
    st.write('Status: **' + ticket['status'].capitalize() + '**')
    st.download_button('Download ticket PDF', ticket_pdf(ticket),
                       file_name=ticket['reference'] + '.pdf', mime='application/pdf',
                       key='download_' + ticket['reference'])



def show_quote(quote):
    st.write(f"Cabin fare: **₹{quote['subtotal_paise']/100:,.2f}**")
    gst_label = f"GST ({quote['gst_percent']}%)" if quote['version'] == 2 else 'GST (not recorded on original ticket)'
    st.write(f"{gst_label}: **₹{quote['gst_paise']/100:,.2f}**")
    st.write(f"Other fees (not modelled): **₹{quote['other_fees_paise']/100:,.2f}**")
    st.write(f"Demo total: **₹{quote['total_paise']/100:,.2f}**")
    st.caption(quote['note'])

def render_booking_page(root, flights):
    try:
        store = booking_store(root)
        _render(store, flights)
    except (sqlite3.Error, OSError, StorageError):
        st.error('Demo tickets are temporarily unavailable. Please try again shortly.')
    except ValueError as error:
        st.warning(str(error))


def _render(store, flights):
    view = st.session_state.view
    st.caption(storage_notice())
    if view == 'booking':
        reference = st.session_state.last_ticket
        if reference:
            ticket = store.get(reference)
            if ticket is None:
                st.warning('This demo ticket is no longer available. Please create a new demo booking.')
                st.button('Find flights', on_click=another_ticket, args=(True,), key='missing_find')
                return
            st.success('Your demo booking is confirmed.' if ticket['status'] == 'confirmed' else 'This demo booking is cancelled.')
            summary(ticket)
            st.subheader('Would you like to book another ticket?')
            yes, no = st.columns(2)
            yes.button('Yes, book another ticket', on_click=another_ticket, args=(True,), use_container_width=True)
            no.button("No, I’m done", on_click=another_ticket, args=(False,), use_container_width=True)
            return
        flight = find_flight(flights, st.session_state.selected_flight)
        if not flight:
            st.warning('Please choose a flight from the search results first.')
            st.button('Find flights', on_click=navigate, args=('search',), key='review_find')
            return
        st.subheader('Review your demo booking')
        st.caption('1 · Flight selected   →   2 · Class & passengers   →   3 · Confirm & download')
        st.write(f'**{flight["airline"]} · {flight["from"]} → {flight["to"]}**')
        st.write(f'{flight["date"]} · {flight["departure"]} — {flight["arrival"]} IST')
        if flight.get('arrival_date',flight['date']) != flight['date']:st.caption('Arrives '+flight['arrival_date']+' (next day)')
        cabin = st.radio('Travel class', list(CABINS), horizontal=True, key='travel_class')
        passengers = st.number_input('Passengers', min_value=1, max_value=6, step=1, key='passenger_count')
        st.caption('Cabin fares and seats are simulated. Choose a different seat for each passenger.')
        available = store.available_seats(flight['id'], cabin)
        if len(available) < passengers:
            st.warning('Not enough demo seats remain in this class. Choose another class or flight.')
            st.button('Back to flight results', on_click=navigate, args=('search',))
            return
        names, seats = [], []
        token = st.session_state.booking_token
        for i in range(passengers):
            name_column, seat_column = st.columns(2)
            names.append(name_column.text_input(f'Passenger {i+1} name (English)', value=f'Guest {i+1}', max_chars=60, key=f'name_{token}_{i}'))
            seats.append(seat_column.selectbox(f'Seat for passenger {i+1}', available, index=i, format_func=seat_label, key=f'seat_{token}_{cabin}_{i}'))
        show_quote(fare_quote(flight['price'], passengers, cabin))
        with st.form('confirm_demo', enter_to_submit=False):
            st.caption('This creates a simulated reservation. No payment is required.')
            if st.form_submit_button('Confirm demo booking', type='primary'):
                try:
                    ticket = store.create(flight, passengers, st.session_state.booking_token, cabin=cabin, passenger_names=names, seats=seats)
                except (ValueError, RuntimeError) as error:
                    st.error(str(error))
                else:
                    ref = ticket['reference']
                    st.session_state.last_ticket = ref
                    if ref not in st.session_state.booking_refs:
                        st.session_state.booking_refs.append(ref)
                    st.rerun()
        st.button('Back to flight results', on_click=navigate, args=('search',))
    elif view == 'tickets':
        st.subheader('My demo tickets')
        st.caption('Tickets created in this browser session. You can look up another ticket with its saved reference.')
        tickets = [store.get(ref) for ref in reversed(st.session_state.booking_refs)]
        tickets = [ticket for ticket in tickets if ticket]
        if not tickets:
            st.info('You haven’t created a demo ticket in this session yet.')
        for ticket in tickets:
            with st.container(border=True):
                summary(ticket)
                if ticket['status'] == 'confirmed':
                    st.button('Cancel this ticket', key='cancel_' + ticket['reference'],
                              on_click=open_cancellation, args=(ticket['reference'],))
        st.button('Look up a ticket by reference', on_click=open_cancellation)
    elif view == 'cancel':
        st.subheader('Find or cancel a demo ticket')
        st.caption('Paste the full reference from your downloaded ticket. Only confirm cancellation after reviewing the details.')
        value = st.text_input('Demo booking reference', key='cancel_reference', placeholder='SKY-XXXX-XXXX-XXXX-XXXX-XXXX')
        try:
            normalized = normalize_reference(value)
        except ValueError:
            normalized = None
        if normalized != st.session_state.cancel_ticket:
            st.session_state.update(cancel_ticket=None, cancel_confirming=False, cancel_notice=None)
        if st.button('Find ticket', type='primary'):
            if not normalized:
                st.warning('Enter the complete SKY reference from your demo ticket.')
            elif store.get(normalized) is None:
                st.warning('No demo ticket was found for that reference. Check the ID; demo records may have reset.')
            else:
                st.session_state.cancel_ticket = normalized
        if st.session_state.cancel_ticket:
            ticket = store.get(st.session_state.cancel_ticket)
            if ticket is None:
                st.warning('That demo record is no longer available.')
                return
            with st.container(border=True):
                summary(ticket)
            if st.session_state.cancel_notice:
                st.success(st.session_state.cancel_notice)
            elif ticket['status'] == 'cancelled':
                st.info('This ticket is already cancelled. There is nothing more to cancel.')
            elif not st.session_state.cancel_confirming:
                st.button('Cancel this demo booking', on_click=set_cancel_confirmation, args=(True,))
            else:
                st.warning('Cancel this demo booking? This will change its status to Cancelled.')
                yes, no = st.columns(2)
                if yes.button('Yes, cancel booking', type='primary', use_container_width=True):
                    _, changed = store.cancel(ticket['reference'])
                    st.session_state.update(cancel_confirming=False, cancel_notice=('Demo booking cancelled. No payment or refund is involved.' if changed else 'This demo booking was already cancelled.'))
                    st.rerun()
                no.button('Keep my booking', on_click=set_cancel_confirmation, args=(False,), use_container_width=True)
