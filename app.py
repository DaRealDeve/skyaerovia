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

st.set_page_config(page_title="SkyAerovia | Skye", page_icon="✈️", layout="wide")
ROOT = Path(__file__).resolve().parent
LOGO = ROOT / "assets" / "logo.jpg"
st.markdown("""
<style>
.stApp { background-color: #F3F6FB; color: #102A43; }
.block-container { max-width: 1080px; padding-top: 2rem; }
[data-testid="stSidebar"] { background-color: #EAF1FA; }
.hero {
    background: linear-gradient(120deg, #071B3A, #145DA0);
    padding: 28px; border-radius: 18px; color: white; margin-bottom: 20px;
}
.hero h1 { color: white; font-size: clamp(28px, 4vw, 42px); padding-top: 0; }
.hero p { color: #E3EEFF; font-size: 17px; margin-bottom: 0; }
.st-key-quick_actions button { color: #145DA0; background: #FFFFFF; border: 1px solid #E0E8F2; justify-content: flex-start; min-height: 46px; }
.st-key-quick_actions button > div, .st-key-quick_actions button span { width: 100%; }
.st-key-quick_actions button p { width: 100%; text-align: left; font-size: 1rem; font-weight: 600; color: #145DA0; }
.st-key-quick_actions button:hover { background: #EAF1FA; border-color: #145DA0; }
.flight-card {
    background: white; padding: 22px; border: 1px solid #D8E4F2;
    border-radius: 14px; margin-bottom: 14px; color: #102A43;
}
.flight-card h3 { color: #071B3A; padding-top: 6px; font-size: 23px; }
.flight-card p { margin-bottom: 8px; }
.flight-card .fare { color: #0B3D91; font-size: 25px; font-weight: 700; }
.flight-card .detail { color: #486581; }
</style>
""", unsafe_allow_html=True)

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
    flights = load_flights(ROOT / "flights.json")
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
    st.caption("Available cities: " + ", ".join(CITIES))

st.markdown("""
<div class="hero">
    <h1>Namaste! Welcome to SkyAerovia</h1>
    <p>Your way through the sky. Find your next journey with Skye.</p>
</div>
""", unsafe_allow_html=True)
st.caption("Student demo · Simulated flights and reservations · No payments")

if flights:
    first_date = min(f["date"] for f in flights)
    last_date = max(f["date"] for f in flights)
    st.caption(f"Sample travel dates: {first_date} to {last_date} · All times are IST")
    if last_date < today.isoformat():
        st.warning("The sample flight dates have expired. The team needs to refresh them before new searches.")
    elif first_date > today.isoformat():
        st.info(f"The sample schedule starts on {first_date}. Choose a date in the displayed range.")
st.subheader("Chat with Skye")
with st.chat_message("assistant"):
    st.write(GREETING)
    with st.container(border=True, key="quick_actions"):
        st.write("**What would you like to do next?**")
        st.button("Find flights", key="nav_search", on_click=navigate, args=("search",), use_container_width=True)
        st.button("My demo tickets", key="nav_tickets", on_click=navigate, args=("tickets",), use_container_width=True)
        st.button("Cancel a ticket", key="nav_cancel", on_click=open_cancellation, use_container_width=True)
if st.session_state.view != "search":
    render_booking_page(ROOT, flights)
    st.stop()
for message in st.session_state.messages[1:]:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("For example: Delhi to Mumbai tomorrow under 5000", max_chars=2000):
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
                    matches = find_matches(flights, state, sort_override, budget_override, stops_override)
                    reply = (
                        f"I found {len(matches)} simulated flight(s) from {state['origin']} to {state['destination']} on {state['date']}."
                        if matches else
                        "No simulated flights match those preferences. Try another date, route or budget."
                    )
        except Exception:
            reply = "I couldn't understand that request. Please try cities and date, for example: Delhi to Mumbai tomorrow."
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()

if flights is not None and st.session_state.results:
    matches = find_matches(flights, st.session_state.results, sort_override, budget_override, stops_override)
    st.divider()
    st.subheader("Your flight options")
    st.caption(f"{len(matches)} simulated flight(s) match the current filters.")
    if not matches:
        st.info("No flights match the current filters. Try allowing stops or increasing your budget.")
    for flight in matches:
        # Escape dataset strings before inserting them into Richa's HTML card design.
        airline, ident, origin, destination, day, departure, arrival = (
            html.escape(str(flight[k])) for k in
            ("airline", "id", "from", "to", "date", "departure", "arrival")
        )
        stops = "Nonstop" if flight["stops"] == 0 else f"{flight['stops']} stop(s)"
        st.markdown(f"""
        <div class="flight-card">
            <p class="detail">{airline} · {ident}</p>
            <h3>{origin} → {destination}</h3>
            <p>{day} · {departure} — {arrival} IST</p>
            <p class="detail">{flight['duration']} minutes · {stops}</p>
            <p class="fare">₹{flight['price']:,}</p>
            <p class="detail">Economy base fare, before GST. Choose your travel class when booking.</p>
        </div>
        """, unsafe_allow_html=True)
        departed = departure_time(flight) <= datetime.now(ZoneInfo("Asia/Kolkata"))
        st.button("Book demo ticket", key="book_" + flight["id"], type="primary",
                  disabled=departed, on_click=start_booking, args=(flight["id"],))
        if departed:
            st.caption("This departure time has passed. Choose a later flight to create a demo ticket.")

