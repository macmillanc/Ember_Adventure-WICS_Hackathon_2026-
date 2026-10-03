import csv
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from pathlib import Path
import requests


# ============================================================
# CONSTANTS
# ============================================================

API_BASE_URL = "https://api.ember.to/v1"

TARGET_CITIES = [
    "Edinburgh",
    "Glasgow",
    "Dundee",
    "Aberdeen",
    "Perth"
]


# ============================================================
# EMBER LOCATIONS
# ============================================================


#RETURNS:
# hubs The id, the lat and longitude 
def fetch_hub_locations():
    """
    Fetch the main Ember stop areas for the cities used
    by the trip planner.
    """
<<<<<<< HEAD
    url = f"{API_BASE_URL}/locations/search/"
    params = {"type": "STOP_AREA"} 

    # Hardcoded coordinates since the search API omits them for these areas
    hardcoded_coords = {
        "Edinburgh (City Centre)": {"lat": 55.9533, "lon": -3.1883},
        "Glasgow Bus Station": {"lat": 55.8642, "lon": -4.2518},
        "Dundee (City Centre)": {"lat": 56.4620, "lon": -2.9707},
        "Aberdeen (City Centre)": {"lat": 57.1497, "lon": -2.0943},
        "Perth (City Centre)": {"lat": 56.3959, "lon": -3.4312},
    }
    
    response = requests.get(url, params=params)
=======

    url = f"{API_BASE_URL}/locations/"

    params = {
        "type": "STOP_AREA"
    }

    response = requests.get(
        url,
        params=params
    )

>>>>>>> 820e61bfb2a5782c2aae13c63e2882fe401f94db
    response.raise_for_status()

    all_locations = response.json()

    hubs = {}

    for loc in all_locations:
<<<<<<< HEAD
        name = loc.get("name", "")
        # Only process exact matches present in your hardcoded dictionary
        if name in hardcoded_coords:
            hubs[name] = {
                "id": loc["id"],
                "lat": hardcoded_coords[name]["lat"],
                "lon": hardcoded_coords[name]["lon"],
            }
            
=======

        name = loc.get(
            "name",
            ""
        )

        name_lower = name.lower()

        for city in TARGET_CITIES:

            if city.lower() in name_lower:

                hubs[name] = {
                    "id": loc["id"],
                    "lat": loc.get("lat"),
                    "lon": loc.get("lon")
                }

                break

>>>>>>> 820e61bfb2a5782c2aae13c63e2882fe401f94db
    return hubs
#returns id based on the location given


def get_id(hubs, location):
    """
    Find the Ember ID for a city.

    Prefer a City Centre stop where one exists.
    """

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


<<<<<<< HEAD


#returns a dictionary

# the keys are the origin id and destination id
# the values in the dictionary are departure time, arrival time , duration in minutes and cost
=======
# ============================================================
# JOURNEYS
# ============================================================

>>>>>>> 820e61bfb2a5782c2aae13c63e2882fe401f94db
def fetch_journeys(origin_id, destination_id):
    """
    Fetch Ember journeys between two locations for today.

    Returns:

        {
            (origin_id, destination_id): [
                journey,
                journey,
                ...
            ]
        }
    """

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
<<<<<<< HEAD
        "departure_date_from": f"{travel_date}T00:00:00",
        "departure_date_to": f"{travel_date}T23:59:59"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    route_key = (origin_id, destination_id)
    journey_list = []
    
    for quote in data.get("quotes", []):
        journey_list.append({
            "departure_time": quote.get("departure_time"),
            "arrival_time": quote.get("arrival_time"),
            "duration_minutes": quote.get("duration_minutes", 0),
            "cost": quote.get("total_price", 0.0) / 100.0
        })
        
    return {
        route_key: journey_list
    }

#returns a List of dictionaries with elements of NAME, CITY, INTEREST, COST, DURATION MIN, LAT and LON
=======
        "departure_date_from": departure_from.isoformat(),
        "departure_date_to": departure_to.isoformat()
    }

    response = requests.get(
        url,
        params=params
    )

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

    quotes = data.get(
        "quotes",
        []
    )

    journey_list = []

    for quote in quotes:

        legs = quote.get(
            "legs",
            []
        )

        if not legs:
            continue

        leg = legs[0]

        departure = leg.get(
            "departure",
            {}
        )

        arrival = leg.get(
            "arrival",
            {}
        )

        departure_time = (
            departure.get("scheduled")
            or departure.get("estimated")
        )

        arrival_time = (
            arrival.get("scheduled")
            or arrival.get("estimated")
        )

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

        prices = quote.get(
            "prices",
            {}
        )

        cost = prices.get(
            "adult",
            0
        ) / 100

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


# ============================================================
# ATTRACTIONS CSV
# ============================================================

>>>>>>> 820e61bfb2a5782c2aae13c63e2882fe401f94db
def load_attractions_csv(filepath=None):
    """
    Load attractions from data/attractions.csv.
    """

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
                    "interest": row["interests"].lower(),
                    "cost": float(row["cost_gbp"]),
                    "duration_minutes": int(
                        row["duration_minutes"]
                    ),
                    "lat": float(row["latitude"]),
                    "lon": float(row["longitude"])
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


<<<<<<< HEAD
#Returns the departure time, minutes and cost

def get_next_bus(journeys_data, origin_id, destination_id, current_time_str):
=======
# ============================================================
# NEXT BUS
# ============================================================

def get_next_bus(
    journeys_data,
    origin_id,
    destination_id,
    current_time_str
):
>>>>>>> 820e61bfb2a5782c2aae13c63e2882fe401f94db
    """
    Find the first journey departing at or after
    current_time_str.
    """

    # --------------------------------------------------------
    # Get journeys for this route
    # --------------------------------------------------------

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
            and journey.get("destination") == destination_id
        ]

<<<<<<< HEAD










#for testing purposes, run to see how the format of everything looks

if __name__ == "__main__":
    print("--- TEST 1: Fetching Live Hub Locations ---")
    try:
        hubs = fetch_hub_locations()
        print(f"Successfully loaded {len(hubs)} hubs:")
        for name, data in hubs.items():
            print(f" - {name}: ID={data['id']}, Lat={data['lat']}, Lon={data['lon']}")
    except Exception as e:
        print(f"Failed to fetch hubs: {e}")

    print("\n--- TEST 2: Testing Attractions CSV Loading ---")
    attractions = load_attractions_csv()
    if attractions:
        print(f"Loaded sample attraction: {attractions[0]}")

    print("\n--- TEST 3: Testing Next Bus Logic (Dummy Data) ---")
    dummy_journeys = [
        {
            "origin": "Edinburgh", 
            "destination": "Glasgow", 
            "departure_time": "2026-10-03T10:30:00", 
            "duration_minutes": 75, 
            "cost": 12.50
        },
        {
            "origin": "Edinburgh", 
            "destination": "Glasgow", 
            "departure_time": "2026-10-03T11:45:00", 
            "duration_minutes": 75, 
            "cost": 12.50
        }
    ]
    
    next_bus = get_next_bus(
        journeys_data=dummy_journeys, 
        origin_id="Edinburgh", 
        destination_id="Glasgow", 
        current_time_str="2026-10-03T11:00:00"
=======
    print(
        f"Searching {len(journey_list)} journeys "
        f"for {origin_id} -> {destination_id}"
>>>>>>> 820e61bfb2a5782c2aae13c63e2882fe401f94db
    )

    # --------------------------------------------------------
    # Parse current time
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Find future buses
    # --------------------------------------------------------

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

                departure_time = datetime.fromisoformat(
                    departure
                )

            except ValueError:

                continue

        else:
            continue

        # ----------------------------------------------------
        # Make timezone information consistent
        # ----------------------------------------------------

        if (
            departure_time.tzinfo is None
            and current_time.tzinfo is not None
        ):

            departure_time = departure_time.replace(
                tzinfo=current_time.tzinfo
            )

        elif (
            current_time.tzinfo is None
            and departure_time.tzinfo is not None
        ):

            current_time = current_time.replace(
                tzinfo=departure_time.tzinfo
            )

        # ----------------------------------------------------
        # Is this bus still in the future?
        # ----------------------------------------------------

        if departure_time >= current_time:

            valid_options.append(
                (
                    departure_time,
                    journey
                )
            )

    # --------------------------------------------------------
    # No future journeys
    # --------------------------------------------------------

    if not valid_options:

        print(
            f"No future journeys found for "
            f"{origin_id} -> {destination_id}"
        )

        return None

    # --------------------------------------------------------
    # Sort by departure
    # --------------------------------------------------------

    valid_options.sort(
        key=lambda item: item[0]
    )

    next_bus = valid_options[0][1]

    print(
        "Next bus:",
        next_bus["departure_time"],
        "->",
        next_bus["arrival_time"],
        ",",
        round(next_bus["duration_minutes"]),
        "min, £",
        round(next_bus["cost"], 2)
    )

    return next_bus