> Baseline documentation: this file describes the original deployed version. The first booking/cancellation upgrade is documented in [upgrade-plan.md](upgrade-plan.md). The saved baseline report/deck/video remain historical artifacts.

# SkyAerovia demo walkthrough

Video format: a captioned walkthrough using screenshots of the verified hosted app, captured on 12 October 2026. The video has no audio and is not a continuous screen recording. Use the narration below when presenting it. No API key appears in it.

Public app: https://skyaerovia.streamlit.app/

## Narration

### 1. SkyAerovia with Skye

Welcome to Sky Aero Via, our student flight search project. The chatbot is called Skye. This walkthrough uses screenshots captured from the hosted app on the twelfth of October, twenty twenty six. Our app searches sixty simulated flights across eight Indian cities. It shows sample schedules and fares. It does not book tickets or accept payments.

### 2. A complete search

Here we type: Delhi to Mumbai tomorrow under five thousand. Skye collects the departure city, destination, date and maximum price. On the capture date, tomorrow means the thirteenth of October. The app finds three simulated flights. Gemini understands the request, and Python searches the stored flight data.

### 3. Matching flight cards

Each card shows the airline, route, date, departure and arrival times, duration, stops and price. The lowest priced option costs three thousand two hundred rupees and has one stop. Two other choices are nonstop. Sorting by shortest duration puts the faster journey first.

### 4. Nonstop filtering

We select Nonstop only in the sidebar. The connecting flight disappears, and two choices remain. Their simulated prices are three thousand nine hundred and four thousand two hundred eighty rupees. The sidebar can override a preference from the chat.

### 5. Budget limits and recovery

Now we set the maximum price to three thousand five hundred rupees, while keeping nonstop enabled. No flights meet both conditions. The app displays a useful recovery message. Allowing stops would bring back the three thousand two hundred rupee flight. A failed search leaves the app usable.

### 6. Questions for missing details

A user can also build a request over several messages. When we send from Delhi, Skye asks which city we are flying to. We answer Mumbai, and it asks for the date. The next date completes the search. Earlier details stay in the current conversation.

### 7. A clean conversation

Clear chat removes the messages and results, and restores the sidebar defaults. Our hosted checks cover these flows, and a separate meaning based request verifies Gemini on the deployment. The public demo is available at sky aero via dot streamlit dot app. Before a later demonstration, the team needs to refresh the sample schedule. Thank you.

## If you present the app live

1. Open the public link and show the simulated-data label and available date range.
2. Click Clear chat.
3. Enter Delhi to Mumbai on 2026-10-13 under 5000. This matches the captured schedule. On another day, use a valid date from the displayed range.
4. Show three results, then choose Nonstop only and show two results.
5. Sort by Shortest duration and show 130 minutes before 140 minutes.
6. Set maximum price to 3500 with nonstop enabled. Explain the no-results message.
7. Allow stops to show the 3200 option.
8. Clear chat and send from Delhi, Mumbai, then a supported date in separate messages.
9. Explain Gemini extraction, validation, JSON search and the keyword fallback.
10. Refresh and commit flights.json before a later demo if the date range has expired.

The PDF report and editable presentation contain the detailed implementation, tests, team coverage and current limitations. Add any institution-specific cover details before submission.
