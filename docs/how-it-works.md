# How SkyAerovia works

Skye is a flight-search chatbot in a Streamlit app. The app searches simulated data; it does not book tickets.

1. **You describe a journey.** For example, “Delhi to Mumbai tomorrow under 5000.” app.py displays and stores the messages in the current browser session.
2. **The extractor collects details.** extractor.py sends the request, today's IST date and known trip details to Gemini, asking for structured JSON. If the AI fails, a simpler keyword parser handles supported phrases.
3. **Python checks the details.** integration.py validates the cities, date, budget and preferences. Missing details trigger a short question. Answers can complete the earlier request.
4. **The search reads the schedule.** search.py filters flights.json by route and date, then applies the maximum price and nonstop preferences. It sorts by price or duration.
5. **The interface shows flight cards.** Cards contain the route, airline, date, times, duration, stops and fare. Sidebar choices override corresponding chat preferences.
6. **You refine or reset the search.** A later message can change a preference. Clear chat removes messages, saved trip details, results and sidebar choices.

On 12 October 2026, “tomorrow” means 2026-10-13 in IST. Delhi → Mumbai under INR 5,000 returns three demo flights: INR 3,200 with one stop, INR 3,900 nonstop and INR 4,280 nonstop. Nonstop filtering removes the connecting flight.

flights.json contains 60 simulated flights covering eight Indian cities and selected routes. The current schedule is 12–18 October 2026. scripts/generate_flights.py can create the next seven days; the refreshed file must be committed for Streamlit Cloud to read it.

The API key is stored privately in Streamlit Secrets. The GitHub repository remains private while the demo app is public at https://skyaerovia.streamlit.app/.
