import os
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import streamlit as st
from extractor import extract_request
from integration import CITIES, find_matches, load_flights, prepare_request

st.set_page_config(page_title="SkyAerovia | Skye", page_icon="✈️")
ROOT = Path(__file__).parent
if (ROOT / "assets/logo.jpg").exists():
    st.image(str(ROOT / "assets/logo.jpg"), width=400)
st.title("SkyAerovia")
st.caption("Your way through the sky")
st.info("Student demo · Simulated flights · No ticket booking or payments")
# The current extractor reads its key from the environment.
if not os.getenv("GEMINI_API_KEY"):
    try:
        key = st.secrets.get("GEMINI_API_KEY")
        if isinstance(key, str) and key.strip():
            os.environ["GEMINI_API_KEY"] = key.strip()
    except st.errors.StreamlitSecretNotFoundError:
        pass
today = datetime.now(ZoneInfo("Asia/Kolkata")).date()
try:
    flights = load_flights(ROOT / "flights.json")
except (ValueError, TypeError, OSError):
    flights = None
    st.error("Flight data could not be loaded. Please try again after the team updates it.")
else:
    if flights is None:
        st.warning("Flight results are waiting for the demo data. You can still tell Skye your travel preferences.")
GREETING = "Hi! I'm Skye. Tell me your departure city, destination and date, and optionally your budget or preference for nonstop flights."
for key, default in (("messages", [{"role": "assistant", "content": GREETING}]), ("request", {}), ("results", None)):
    if key not in st.session_state:
        st.session_state[key] = default
if st.sidebar.button("New chat"):
    st.session_state.messages = [{"role": "assistant", "content": GREETING}]
    st.session_state.request = {}
    st.session_state.results = None
    st.rerun()
st.sidebar.header("Search preferences")
sort_choice = st.sidebar.selectbox("Sort flights", ["Use chat preference", "Lowest price", "Shortest duration"])
sort_override = {"Lowest price": "price", "Shortest duration": "duration"}.get(sort_choice)
use_budget = st.sidebar.checkbox("Set maximum price")
budget_override = st.sidebar.number_input("Maximum price (₹)", min_value=0, value=5000, step=500) if use_budget else None
stops_choice = st.sidebar.selectbox("Stops", ["Use chat preference", "Nonstop only", "Allow stops"])
stops_override = {"Nonstop only": True, "Allow stops": False}.get(stops_choice)
st.sidebar.caption("Available cities: " + ", ".join(CITIES))
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
if prompt := st.chat_input("Message Skye", max_chars=2000):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.results = None
    with st.spinner("Skye is checking your request…"):
        try:
            state, status, reply = prepare_request(prompt, st.session_state.request, today, extract_request)
            st.session_state.request = state
            if status == "ready":
                if flights is None:
                    reply = f"Your request is {state['origin']} to {state['destination']} on {state['date']}. Flight results are waiting for the demo data."
                else:
                    st.session_state.results = state
                    matches = find_matches(flights, state, sort_override, budget_override, stops_override)
                    reply = f"I found {len(matches)} simulated flight(s) from {state['origin']} to {state['destination']} on {state['date']}." if matches else "No simulated flights match those preferences. Try another date, route or budget."
        except Exception:
            reply = "I couldn't understand that request. Please try cities and date, for example: Delhi to Mumbai tomorrow."
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.rerun()
if flights is not None and st.session_state.results:
    matches = find_matches(flights, st.session_state.results, sort_override, budget_override, stops_override)
    st.subheader("Simulated flight results")
    st.caption("Times are in IST. Sidebar choices override the corresponding chat preferences.")
    if not matches:
        st.write("No flights match the current filters.")
    for flight in matches:
        with st.container(border=True):
            st.write(f"**{flight['airline']} · {flight['id']}**")
            st.write(f"{flight['from']} → {flight['to']} · {flight['date']}")
            st.write(f"{flight['departure']} → {flight['arrival']} · {flight['duration']} minutes · {flight['stops']} stop(s)")
            st.write(f"**₹{flight['price']:,}**")
