
import streamlit as st

st.set_page_config(
    page_title="SkyAerovia \| Skye",
    page_icon="✈️",
    layout="wide"
)
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    st.image("assets/logo.jpg", width=700)

#Navy and blue theme
st.markdown("""
<style>
.stApp {
    background-color: #F3F6FB;
}

.hero {
    background: linear-gradient(120deg, #071B3A, #145DA0);
    padding: 12px;
    border-radius: 15px;
    color: white;
    margin-bottom: 15px;
}

.hero h1 {
    color: white;
    font-size: 24px;
}

.hero p {
    color: #E3EEFF;
    font-size: 16px;
}

.flight-card {
    background: white;
    padding: 20px;
    border: 1px solid #D8E4F2;
    border-radius: 12px;
    margin-bottom: 15px;
    color: #102A43;
}
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.image("assets/logo.jpg", width=320)
    st.caption("Your personal travel assistant")
    st.divider()
    st.subheader("Flight preferences")

    sort_by = st.selectbox(
        "Sort flights by",
        ["Recommended", "Lowest price", "Shortest duration"]
    )

    nonstop = st.checkbox("Non-stop flights only")

    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.rerun()

# Welcome banner
st.markdown("""
<div class="hero">
    <h1>Namaste! Welcome to SkyAerovia</h1>
    <p>Your journey begins here. How can we help you fly today?</p>
</div>
""", unsafe_allow_html=True)

# Chat section
if "messages" not in st.session_state:
    st.session_state.messages = []

st.markdown(
    '<h3 style="color: #0B3D91;">☁️Chat with your travel assistant</h3>',
    unsafe_allow_html=True
)

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input(
    "Ask about flights, timings or travel plans..."
)

if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.spinner("Preparing your response..."):
        response = (
            "Welcome aboard! This is a UI demo. "
            "Your team's AI backend will be connected later."
        )

    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    st.rerun()

# Flight cards
st.divider()
st.markdown(
    '<h3 style="color: #0B3D91;"> ✈️Explore Flights</h3>',
    unsafe_allow_html=True
)

st.caption("Sample flights for design demonstration only")

flights = [
    {
        "flight": "AI 101",
        "departure": "08:30 AM",
        "arrival": "10:45 AM",
        "duration": 135,
        "price": 5500,
        "stops": 0
    },
    {
        "flight": "AI 865",
        "departure": "11:00 AM",
        "arrival": "01:45 PM",
        "duration": 165,
        "price": 4200,
        "stops": 1
    },
    {
        "flight": "AI 678",
        "departure": "05:00 PM",
        "arrival": "07:10 PM",
        "duration": 130,
        "price": 6100,
        "stops": 0
    }
]

if nonstop:
    flights = [f for f in flights if f["stops"] == 0]

if sort_by == "Lowest price":
    flights.sort(key=lambda f: f["price"])
elif sort_by == "Shortest duration":
    flights.sort(key=lambda f: f["duration"])

for flight in flights:
    stops_text = "Non-stop" if flight["stops"] == 0 else "1 stop"

    st.markdown(f"""
    <div class="flight-card">
        <p><b> SkyAerovia· {flight["flight"]}</b></p>
        <h3>Delhi (DEL) → Mumbai (BOM)</h3>
        <p>{flight["departure"]} — {flight["arrival"]}</p>
        <p>{flight["duration"]} minutes · {stops_text}</p>
        <h3>₹{flight["price"]:,}</h3>
    </div>
    """, unsafe_allow_html=True)
