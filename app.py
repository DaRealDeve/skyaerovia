"""SkyAerovia: Richa's navy/blue frontend connected to Skye and demo search."""
import html
import os
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st

from extractor import extract_request
from integration import CITIES, find_matches, load_flights, prepare_request
from booking_ui import navigate, start_booking, open_cancellation, render_booking_page
from bookings import departure_time
from schedule import load_app_flights
from city_catalog import AIRLINES
from flight_ui import CSS, schedule_header, search_form, filtered_matches, empty_message, cards
from account_ui import render_accounts, go_account, log_out, account_intent

st.set_page_config(page_title="SkyAerovia | Skye", page_icon="✈️", layout="wide")
ROOT = Path(__file__).resolve().parent
LOGO = ROOT / "assets" / "logo.jpg"
st.markdown(CSS, unsafe_allow_html=True)

# Read credentials only from the environment or private Streamlit secrets.
for setting in ("GEMINI_API_KEY", "GEMINI_MODEL"):
    if not os.getenv(setting):
        try:
            value = st.secrets.get(setting)
            if isinstance(value, str) and value.strip():
                os.environ[setting] = value.strip()
        except st.errors.StreamlitSecretNotFoundError:
            pass
# The extractor's model setting is evaluated at import. Apply a Cloud secret override.
import extractor
if os.getenv("GEMINI_MODEL"):
    extractor.MODEL = os.environ["GEMINI_MODEL"]

today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
try:
    flights = load_app_flights(ROOT, today)
except (ValueError, TypeError, OSError):
    flights = None
    st.error("Flight data could not be loaded. Please try again after the team updates it.")
else:
    if flights is None:
        st.warning("Flight results are waiting for the demo data. You can still tell Skye your travel preferences.")

GREETING = "Namaste! I'm Skye, your SkyAerovia flight assistant. Tell me your departure city, destination and travel date. You can also ask for a budget, nonstop flights or the shortest journey."
for name, default in (
    ("messages", [{"role": "assistant", "content": GREETING}]),
    ("request", {}), ("results", None), ("view", "search"), ("booking_refs", []),
    ("selected_flight", None), ("last_ticket", None), ("cancel_reference", ""),
    ("cancel_ticket", None), ("cancel_confirming", False), ("cancel_notice", None)
):
    if name not in st.session_state:
        st.session_state[name] = default

with st.sidebar:
    if LOGO.exists():
        st.image(str(LOGO), width=230)
    st.caption("Your way through the sky")
    st.divider()
    if st.button("Clear chat", key="clear_chat", use_container_width=True):
        st.session_state.messages = [{"role": "assistant", "content": GREETING}]
        st.session_state.request = {}
        st.session_state.results = None
        st.session_state.view = "search"
        # Set widget values explicitly so the browser also resets its controls.
        st.session_state.sort_choice = "Use chat preference"
        st.session_state.budget_enabled = False
        st.session_state.budget_value = 5000
        st.session_state.stops_choice = "Use chat preference"
        st.session_state.airline_choices = []
        st.session_state.time_choice = "Any time"
        st.session_state.preferred_cabin = "Economy"
        st.rerun()
    st.subheader("Flight preferences")
    st.caption("Clear chat keeps your demo tickets.")
    sort_choice = st.selectbox(
        "Sort flights", ["Use chat preference", "Lowest price", "Shortest duration"],
        key="sort_choice"
    )
    sort_override = {"Lowest price": "price", "Shortest duration": "duration"}.get(sort_choice)
    use_budget = st.checkbox("Set maximum price", key="budget_enabled")
    budget_override = st.number_input(
        "Maximum base fare (₹)", min_value=1, value=5000, step=500, key="budget_value"
    ) if use_budget else None
    stops_choice = st.selectbox(
        "Stops", ["Use chat preference", "Nonstop only", "Allow stops"], key="stops_choice"
    )
    stops_override = {"Nonstop only": True, "Allow stops": False}.get(stops_choice)
    st.caption("Choose a filter here to override the same preference in your chat.")
    st.divider()
    preferred_cabin = st.selectbox("Preferred class", ["Economy", "Premium Economy", "Business"], key="preferred_cabin")
    st.multiselect("Airlines", AIRLINES, key="airline_choices", placeholder="All airlines")
    st.selectbox("Departure time", ["Any time", "Morning (05–12)", "Afternoon (12–17)", "Evening (17–22)", "Late night (22–05)"], key="time_choice")
    with st.expander("See all departure cities"):
        st.write(", ".join(CITIES))
    st.caption("All routes, fares and airline schedules are simulated.")

st.markdown("""
<div class="hero">
    <h1>Namaste! Welcome to SkyAerovia</h1>
    <p>Your way through the sky. Find your next journey with Skye.</p>
</div>
""", unsafe_allow_html=True)
st.caption("Student demo · Simulated flights and reservations · No payments")

first_day, last_day = schedule_header(flights, today)
if st.session_state.view == "search":
    search_form(first_day, last_day, today)
st.subheader("Chat with Skye")
with st.chat_message("assistant"):
    st.write(GREETING)
    account_user = render_accounts()
    with st.container(border=True, key="quick_actions"):
        st.write("**What would you like to do next?**")
        if account_user:
            st.button("Log out", key="nav_logout", on_click=log_out, use_container_width=True)
        else:
            st.button("Log in", key="nav_login", on_click=go_account, args=("login",), use_container_width=True)
            st.button("Register", key="nav_register", on_click=go_account, args=("register",), use_container_width=True)
        st.button("Find flights", key="nav_search", on_click=navigate, args=("search",), use_container_width=True)
        st.button("My demo tickets", key="nav_tickets", on_click=navigate, args=("tickets",), use_container_width=True)
        st.button("Cancel a ticket", key="nav_cancel", on_click=open_cancellation, use_container_width=True)
if st.session_state.view in ("login", "register"):
    st.stop()
if st.session_state.view != "search":
    render_booking_page(ROOT, flights)
    st.stop()
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("For example: Delhi to Mumbai tomorrow under 5000", max_chars=2000):
    # Account commands open secure fields without recording credentials in chat.
    if intent := account_intent(prompt):
        go_account(intent)
        st.rerun()
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Guest ticket actions are deterministic and never delegated to the AI.
    if re.search(r"\b(?:cancel|cancellation)\b", prompt, re.IGNORECASE):
        open_cancellation()
        reference = re.search(r"SKY-(?:[0-9a-f]{4}-){4}[0-9a-f]{4}", prompt, re.IGNORECASE)
        if reference:
            st.session_state.cancel_reference = reference.group(0)
        st.session_state.messages.append({"role": "assistant", "content": "Enter your saved demo reference, review the ticket, then confirm cancellation."})
        st.rerun()
    st.session_state.results = None
    with st.spinner("Skye is checking your request…"):
        try:
            state, status, reply = prepare_request(
                prompt, st.session_state.request, today, extract_request
            )
            st.session_state.request = state
            if status == "ready":
                if flights is None:
                    reply = f"Your request is {state['origin']} to {state['destination']} on {state['date']}. Flight results are waiting for the demo data."
                else:
                    st.session_state.results = state
                    matches = filtered_matches(flights, state, sort_override, budget_override, stops_override)
                    reply = (
                        f"I found {len(matches)} simulated flight(s) from {state['origin']} to {state['destination']} on {state['date']}."
                        if matches else
                        empty_message(flights, state)
                    )
        except Exception:
            reply = "I couldn't understand that request. Please try cities and date, for example: Delhi to Mumbai tomorrow."
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

if flights is not None and st.session_state.results:
    cards(flights,st.session_state.results,sort_override,budget_override,stops_override,preferred_cabin)
