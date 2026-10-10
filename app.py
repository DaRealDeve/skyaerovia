from pathlib import Path

import streamlit as st

st.set_page_config(page_title="SkyAerovia | Skye", page_icon="✈️")

logo = Path(__file__).parent / "assets" / "logo.jpg"
if logo.exists():
    st.image(str(logo), width=400)
st.title("SkyAerovia")
st.caption("Your way through the sky")
st.info("Student prototype. Flight search and Gemini integration are coming soon. Flight data will be simulated.")

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hi! I'm Skye, your SkyAerovia flight assistant. The team is building flight search, comparisons and travel FAQs."}
    ]

if st.sidebar.button("New chat"):
    del st.session_state.messages
    st.rerun()

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

if prompt := st.chat_input("Message Skye", max_chars=2000):
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.session_state.messages.append({
        "role": "assistant",
        "content": "This is our starter chat interface. Flight search and AI responses are not connected yet. When ready, I'll help you search by departure city, destination and date."
    })
    st.rerun()
