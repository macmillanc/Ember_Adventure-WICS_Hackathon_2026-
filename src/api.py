import csv
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from pathlib import Path
import requests

API_BASE_URL = "https://api.ember.to/v1"
TARGET_CITIES = [
    "Edinburgh",
    "Glasgow",
    "Dundee",
    "Aberdeen",
    "Perth"
]


def fetch_hub_locations():
    url = f"{API_BASE_URL}/locations/"
    params = {"type": "STOP_AREA"}

    response = requests.get(url, params=params)
    response.raise_for_status()

    all_locations = response.json()

    hubs = {}

    for loc in all_locations:
        name = loc.get("name", "")
        name_lower = name.lower()

        for city in TARGET_CITIES:
            if city.lower() in name_lower:
                hubs[name] = {
                    "id": loc["id"],
                    "lat": loc.get("lat"),
                    "lon": loc.get("lon")
                }
                break

    return hubs


def get_id(hubs, location):
    for name, data in hubs.items():
        if (
            location.lower() in name.lower()
            and "city centre" in name.lower()
        ):
            return data["id"]

    for name, data in hubs.items():
        if location.lower() in name.lower():
            return data["id"]

    return None


def fetch_journeys(origin_id, destination_id):
    travel_date = date.today()
    tz = ZoneInfo("Europe/London")

    departure_from = datetime.combine(
        travel_date,
        time.min,
        tzinfo=tz
    )

    departure_to = datetime.combine(
        travel_date,
        time.max,
        tzinfo=tz
    )

    url = f"{API_BASE_URL}/quotes/"

    params = {
        "origin": origin_id,
        "destination": destination_id,
        "departure_date_from": departure_from.isoformat(),
        "departure_date_to": departure_to.isoformat()
    }

    response = requests.get(url, params=params)

    if response.status_code == 429:
        print(
            f"Rate limited by Ember: "
            f"{origin_id} -> {destination_id}"
        )
        return {
            (origin_id, destination_id): []
        }

    if response.status_code in (400, 404):
        print(
            f"Ember rejected route "
            f"{origin_id} -> {destination_id}: "
            f"{response.status_code}"
        )
        print(response.text)

        return {
            (origin_id, destination_id): []
        }

    response.raise_for_status()

    data = response.json()

    quotes = data.get("quotes", [])

    journey_list = []

    for quote in quotes:
        legs = quote.get("legs", [])

        if not legs:
            continue

        leg = legs[0]

        departure = leg.get("departure", {})
        arrival = leg.get("arrival", {})

        departure_time = departure.get("scheduled")
        arrival_time = arrival.get("scheduled")

        if not departure_time or not arrival_time:
            continue

        try:
            departure_dt = datetime.fromisoformat(
                departure_time
            )

            arrival_dt = datetime.fromisoformat(
                arrival_time
            )

            duration_minutes = (
                arrival_dt - departure_dt
            ).total_seconds() / 60

        except (ValueError, TypeError):
            continue

        prices = quote.get("prices", {})

        cost = prices.get("adult", 0) / 100

        journey_list.append({
            "origin": origin_id,
            "destination": destination_id,
            "departure_time": departure_time,
            "arrival_time": arrival_time,
            "duration_minutes": duration_minutes,
            "cost": cost
        })

    print(
        f"Found {len(journey_list)} usable journeys "
        f"for {origin_id} -> {destination_id}"
    )

    return {
        (origin_id, destination_id): journey_list
    }


def load_attractions_csv(filepath=None):
    if filepath is None:
        script_dir = Path(__file__).resolve().parent

        filepath = (
            script_dir.parent
            / "data"
            / "attractions.csv"
        )

    attractions = []

    try:
        with open(
            filepath,
            mode="r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:
                attractions.append({
                    "id": row["id"],
                    "name": row["attraction"],
                    "city": row["destination"],
                    "interest":
                        row["interests"].lower(),
                    "cost":
                        float(row["cost_gbp"]),
                    "duration_minutes":
                        int(row["duration_minutes"]),
                    "lat":
                        float(row["latitude"]),
                    "lon":
                        float(row["longitude"])
                })

        print(
            f"Successfully loaded "
            f"{len(attractions)} attractions."
        )

    except FileNotFoundError:
        print(
            f"ERROR: Could not find "
            f"attractions.csv at {filepath}"
        )

    except KeyError as e:
        print(
            f"ERROR: Missing expected "
            f"column in CSV: {e}"
        )

    return attractions


def get_next_bus(
    journeys_data,
    origin_id,
    destination_id,
    current_time_str
):
    if isinstance(journeys_data, dict):

        route_key = (
            origin_id,
            destination_id
        )

        journey_list = journeys_data.get(
            route_key,
            []
        )

    else:

        journey_list = [
            journey
            for journey in journeys_data
            if journey.get("origin") == origin_id
            and journey.get("destination")
            == destination_id
        ]

    print(
        f"Searching {len(journey_list)} journeys "
        f"for {origin_id} -> {destination_id}"
    )

    try:
        current_time = datetime.fromisoformat(
            current_time_str
        )

    except Exception as e:

        print(
            "Could not parse current time:",
            current_time_str
        )

        print(e)

        return None

    valid_options = []

    for journey in journey_list:

        departure = journey.get(
            "departure_time"
        )

        if not departure:
            continue

        if isinstance(
            departure,
            datetime
        ):

            departure_time = departure

        elif isinstance(
            departure,
            str
        ):

            try:
                departure_time = (
                    datetime.fromisoformat(
                        departure
                    )
                )

            except ValueError:

                print(
                    "Could not parse departure:",
                    departure
                )

                continue

        else:
            continue

        if (
            departure_time.tzinfo is None
            and current_time.tzinfo is not None
        ):
            departure_time = (
                departure_time.replace(
                    tzinfo=current_time.tzinfo
                )
            )

        elif (
            current_time.tzinfo is None
            and departure_time.tzinfo is not None
        ):
            current_time = (
                current_time.replace(
                    tzinfo=departure_time.tzinfo
                )
            )

        if departure_time >= current_time:
            valid_options.append(
                (
                    departure_time,
                    journey
                )
            )

    if not valid_options:

        print(
            f"No future journeys found "
            f"for {origin_id} -> {destination_id}"
        )

        if journey_list:

            print(
                "Available departure times:"
            )

            for journey in journey_list[:10]:

                print(
                    "  ",
                    journey.get(
                        "departure_time"
                    )
                )

        return None

    valid_options.sort(
        key=lambda item: item[0]
    )

    next_bus = valid_options[0][1]

    print(
        "Next bus:",
        next_bus
    )

    return next_bus