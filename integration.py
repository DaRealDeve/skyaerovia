"""Connect extractor output, conversation state and flight search."""
import json
import math
from datetime import date
from pathlib import Path
from search import search_flights

CITIES = ("Delhi", "Mumbai", "Bengaluru", "Chennai", "Hyderabad", "Kolkata", "Pune", "Ahmedabad")
FIELDS = ("origin", "destination", "date", "sort_by", "max_price", "non_stop")
HELP = "Tell me your departure city, destination and date. You can request cheapest or fastest flights, a budget, or nonstop flights. This demo cannot book tickets."


def load_flights(path):
    path = Path(path)
    if not path.exists():
        return None
    records = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError("flights.json must contain a list")
    required = {"id", "airline", "from", "to", "date", "departure", "arrival", "duration", "stops", "price"}
    seen = set()
    for f in records:
        if not isinstance(f, dict) or not required.issubset(f):
            raise ValueError("Missing flight fields")
        if not isinstance(f["id"], str) or not f["id"] or f["id"] in seen:
            raise ValueError("Invalid or duplicate ID")
        seen.add(f["id"])
        if f["from"] not in CITIES or f["to"] not in CITIES or f["from"] == f["to"]:
            raise ValueError("Unsupported route")
        date.fromisoformat(f["date"])
        for key in ("duration", "price", "stops"):
            v = f[key]
            if isinstance(v, bool) or not isinstance(v, int) or v < (0 if key == "stops" else 1):
                raise ValueError("Invalid " + key)
        for key in ("departure", "arrival"):
            v = f[key]
            if not isinstance(v, str) or len(v) != 5 or v[2] != ":":
                raise ValueError("Invalid time")
            h, m = map(int, v.split(":"))
            if not 0 <= h < 24 or not 0 <= m < 60:
                raise ValueError("Invalid time")
    return records


def prepare_request(message, context, today, extract):
    raw = extract(message, today.isoformat(), dict(context))
    if not isinstance(raw, dict):
        raise ValueError("Extractor must return a dictionary")
    intent = raw.get("intent", "unknown")
    problems = getattr(raw, "problems", {})
    problems = problems if isinstance(problems, dict) else {}
    if intent in ("help", "book_flight", "cancel_booking", "flight_status") and not problems:
        return dict(context), "help", HELP
    state = dict(context)
    supplied = {k: raw[k] for k in FIELDS if raw.get(k) is not None}
    if intent in ("unknown", "other") and not supplied and not problems:
        return state, "help", HELP
    state.update(supplied)
    state["intent"] = "search"
    # An explicit rejected update must clear a previously saved value.
    for field in ("date", "max_price", "sort_by"):
        if field in problems:
            state[field] = None
    if "date" in problems:
        state["asking"] = "date"
        return state, "clarify", "Please give a valid travel date for today or later."
    if "max_price" in problems:
        state["asking"] = "max_price"
        return state, "clarify", "Please give a valid positive maximum budget in rupees."
    if "sort_by" in problems:
        state["asking"] = "sort_by"
        return state, "clarify", "I can sort by price or duration. Which would you prefer?"
    if intent == "cheapest":
        state["sort_by"] = "price"
    if state.get("sort_by") not in (None, "price", "duration"):
        state["sort_by"] = None
        state["asking"] = "sort_by"
        return state, "clarify", "I can sort by price or duration. Which would you prefer?"
    for field in ("origin", "destination"):
        if state.get(field) and state[field] not in CITIES:
            state[field] = None
            state["asking"] = field
            return state, "clarify", "Please choose your " + field + " from: " + ", ".join(CITIES) + "."
    if state.get("date"):
        try:
            d = date.fromisoformat(state["date"])
            if d < today:
                raise ValueError("Past date")
            state["date"] = d.isoformat()
        except (ValueError, TypeError):
            state["date"] = None
            state["asking"] = "date"
            return state, "clarify", "Please give a valid travel date for today or later."
    price = state.get("max_price")
    if price is not None and (isinstance(price, bool) or not isinstance(price, (int, float)) or not math.isfinite(price) or price < 0):
        state["max_price"] = None
        state["asking"] = "max_price"
        return state, "clarify", "Please give a valid maximum budget in rupees."
    if state.get("non_stop") is not None and not isinstance(state["non_stop"], bool):
        state["non_stop"] = None
        return state, "clarify", "Would you like nonstop flights only, or are stops okay?"
    for field, question in (("origin", "Which city are you flying from?"), ("destination", "Which city are you flying to?"), ("date", "What date would you like to travel?")):
        if not state.get(field):
            state["asking"] = field
            return state, "clarify", question
    if state["origin"] == state["destination"]:
        state["destination"] = None
        state["asking"] = "destination"
        return state, "clarify", "Please choose a different destination city."
    state.pop("asking", None)
    return state, "ready", ""


def find_matches(flights, state, sort_override=None, budget_override=None, stops_override=None):
    return search_flights(
        flights, state["origin"], state["destination"], state["date"],
        sort_by=sort_override or state.get("sort_by") or "price",
        max_price=budget_override if budget_override is not None else state.get("max_price"),
        non_stop=stops_override if stops_override is not None else bool(state.get("non_stop")),
    )

