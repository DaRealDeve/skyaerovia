"""Flight search: pure filtering and sorting over an already-loaded flight list.

No UI widgets, no Gemini calls. City alias handling happens before this function.
"""

VALID_SORT_KEYS = ("price", "duration")


def search_flights(flights, origin, destination, date,
                   max_price=None, non_stop=False, sort_by="price"):
    """Return a new list of flights matching the request.

    flights     -- list of dicts with keys: id, from, to, date, price, duration, stops
    origin      -- normalized departure city (exact match on record["from"])
    destination -- normalized arrival city (exact match on record["to"])
    date        -- date string (exact match on record["date"])
    max_price   -- None, or inclusive upper bound on price
    non_stop    -- if True, keep only records with stops == 0
    sort_by     -- "price" or "duration" (numeric, ascending); ties broken by id

    Returns [] if nothing matches. Raises ValueError on invalid arguments.
    The input list and its records are never mutated.
    """
    if not isinstance(flights, list):
        raise ValueError("flights must be a list")
    for name, value in (("origin", origin), ("destination", destination), ("date", date)):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} must be a non-empty string")
    if max_price is not None:
        if isinstance(max_price, bool) or not isinstance(max_price, (int, float)):
            raise ValueError("max_price must be a number or None")
        if max_price < 0:
            raise ValueError("max_price must not be negative")
    if not isinstance(non_stop, bool):
        raise ValueError("non_stop must be True or False")
    if sort_by not in VALID_SORT_KEYS:
        raise ValueError(f"sort_by must be one of {VALID_SORT_KEYS}")

    matches = [
        dict(f) for f in flights
        if f["from"] == origin and f["to"] == destination and f["date"] == date
    ]
    if max_price is not None:
        matches = [f for f in matches if float(f["price"]) <= max_price]
    if non_stop:
        matches = [f for f in matches if int(f["stops"]) == 0]

    matches.sort(key=lambda f: (float(f[sort_by]), f["id"]))
    return matches
