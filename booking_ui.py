"""Guided guest demo booking and cancellation, written for SkyAerovia."""
import secrets
import sqlite3
import streamlit as st
from bookings import BookingStore, normalize_reference, ticket_text


def navigate(view):
    st.session_state.view = view


def start_booking(flight_id):
    st.session_state.update(selected_flight=flight_id, booking_token=secrets.token_hex(16),
                            last_ticket=None, passenger_count=1, view='booking')


def another_ticket(yes):
    st.session_state.update(selected_flight=None, last_ticket=None, view='search' if yes else 'tickets')


def open_cancellation(reference=None):
    st.session_state.update(view='cancel', cancel_reference=reference or '', cancel_ticket=reference,
                            cancel_confirming=False, cancel_notice=None)


def set_cancel_confirmation(value):
    st.session_state.cancel_confirming = value


def summary(ticket):
    f = ticket['flight']
    st.code(ticket['reference'], language=None)
    st.write(f'**{f["airline"]} · {f["from"]} → {f["to"]}**')
    st.write(f'{f["date"]} · {f["departure"]} — {f["arrival"]} IST')
    st.write(f'{ticket["passengers"]} passenger(s) · Sample total ₹{ticket["total"]:,}')
    st.write('Status: **' + ticket['status'].capitalize() + '**')
    st.download_button('Download demo ticket', ticket_text(ticket),
                       file_name=ticket['reference'] + '.txt', mime='text/plain',
                       key='download_' + ticket['reference'])


def render_booking_page(root, flights):
    try:
        store = BookingStore(root / '.data' / 'bookings.sqlite3')
        _render(store, flights)
    except (sqlite3.Error, OSError):
        st.error('Demo tickets are temporarily unavailable. Please try again shortly.')
    except ValueError as error:
        st.warning(str(error))


def _render(store, flights):
    view = st.session_state.view
    st.caption('Demo reservations only. Keep your downloaded reference; records may reset when the app restarts or is redeployed.')
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
        flight = next((f for f in (flights or []) if f['id'] == st.session_state.selected_flight), None)
        if not flight:
            st.warning('Please choose a flight from the search results first.')
            st.button('Find flights', on_click=navigate, args=('search',), key='review_find')
            return
        st.subheader('Review your demo booking')
        st.write(f'**{flight["airline"]} · {flight["from"]} → {flight["to"]}**')
        st.write(f'{flight["date"]} · {flight["departure"]} — {flight["arrival"]} IST')
        st.write(f'Sample fare: **₹{flight["price"]:,} per passenger**')
        passengers = st.number_input('Passengers', min_value=1, max_value=6, step=1, key='passenger_count')
        st.write(f'Sample total: **₹{flight["price"] * passengers:,}**')
        with st.form('confirm_demo', enter_to_submit=False):
            st.caption('This creates a simulated reservation. No payment is required.')
            if st.form_submit_button('Confirm demo booking', type='primary'):
                try:
                    ticket = store.create(flight, passengers, st.session_state.booking_token)
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
