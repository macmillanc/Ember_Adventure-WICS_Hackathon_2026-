from itertools import permutations
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta
from bisect import bisect_left

from api import (
    fetch_hub_locations,
    get_id,
    fetch_journeys,
    load_attractions_csv
)


# ---------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------

TARGET_CITIES = [
    "Edinburgh",
    "Glasgow",
    "Dundee",
    "Aberdeen",
    "Perth"
]

WALKING_SPEED_KMH = 5.0


# ---------------------------------------------------------
# INTEREST HELPERS
# ---------------------------------------------------------

def normalise_interest(interest):
    """
    Normalises interest names so equivalent categories
    are treated as the same thing.
    """

    interest = interest.strip().lower()

    if interest == "hiking":
        return "walking"

    return interest


# ---------------------------------------------------------
# DISTANCE / WALKING
# ---------------------------------------------------------

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    Returns the distance between two coordinates in kilometres.
    """

    earth_radius_km = 6371.0

    lat1 = radians(lat1)
    lon1 = radians(lon1)
    lat2 = radians(lat2)
    lon2 = radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        sin(dlat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(dlon / 2) ** 2
    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return earth_radius_km * c


def walking_time_minutes(distance_km):
    """
    Calculates walking time using the assumed walking speed.
    """

    return (
        distance_km
        / WALKING_SPEED_KMH
        * 60
    )


# ---------------------------------------------------------
# DATETIME HELPERS
# ---------------------------------------------------------

def parse_datetime(value):
    """
    Converts an ISO datetime string to a datetime object.
    """

    if isinstance(value, datetime):
        return value

    return datetime.fromisoformat(value)


# ---------------------------------------------------------
# JOURNEY PREPARATION
# ---------------------------------------------------------

def prepare_journeys(journeys):
    """
    Sorts each route's journeys by departure time.

    This allows get_next_journey() to use binary search
    instead of scanning every journey every time.
    """

    prepared = {}

    for route_key, journey_list in journeys.items():

        sorted_list = sorted(
            journey_list,
            key=lambda journey: parse_datetime(
                journey["departure_time"]
            )
        )

        departure_times = [
            parse_datetime(
                journey["departure_time"]
            )
            for journey in sorted_list
        ]

        prepared[route_key] = {
            "journeys": sorted_list,
            "departure_times": departure_times
        }

    return prepared


def get_next_journey(
    prepared_journeys,
    origin_id,
    destination_id,
    current_time
):
    """
    Returns the first journey departing at or after current_time.
    """

    route_key = (
        origin_id,
        destination_id
    )

    route_data = prepared_journeys.get(
        route_key
    )

    if not route_data:
        return None

    departure_times = route_data[
        "departure_times"
    ]

    journey_list = route_data[
        "journeys"
    ]

    index = bisect_left(
        departure_times,
        current_time
    )

    if index >= len(journey_list):
        return None

    return journey_list[index]


# ---------------------------------------------------------
# ATTRACTION ROUTE
# ---------------------------------------------------------

def calculate_attraction_route(attractions):
    """
    Calculates the total walking distance and walking time
    between consecutive attractions.
    """

    if len(attractions) <= 1:
        return 0.0, 0.0

    total_distance = 0.0
    total_walking_time = 0.0

    for i in range(len(attractions) - 1):

        current = attractions[i]
        next_attraction = attractions[i + 1]

        distance = haversine_distance(
            current["lat"],
            current["lon"],
            next_attraction["lat"],
            next_attraction["lon"]
        )

        total_distance += distance

        total_walking_time += walking_time_minutes(
            distance
        )

    return (
        total_walking_time,
        total_distance
    )


# ---------------------------------------------------------
# TRIP SCORING
# ---------------------------------------------------------

def calculate_trip_score(
    attractions,
    selected_interests,
    total_time_minutes,
    total_cost,
    bus_time_minutes
):
    """
    Calculates the ranking score for a trip.

    Priority order:

    1. Number of relevant attractions
    2. Number of distinct interests covered
    3. Relevant attractions per minute
    4. Lower total time
    5. Lower total cost
    6. Lower bus travel time
    """

    selected_interests = {
        normalise_interest(interest)
        for interest in selected_interests
    }

    matched_attraction_count = 0
    covered_interests = set()

    for attraction in attractions:

        attraction_interests = {
            normalise_interest(interest)
            for interest in attraction["interest"].split(",")
        }

        matched_interests = (
            attraction_interests
            .intersection(selected_interests)
        )

        if matched_interests:
            matched_attraction_count += 1
            covered_interests.update(
                matched_interests
            )

    distinct_interest_count = len(
        covered_interests
    )

    if total_time_minutes > 0:
        interest_efficiency = (
            matched_attraction_count
            / total_time_minutes
        )
    else:
        interest_efficiency = 0

    return (
        matched_attraction_count,
        distinct_interest_count,
        interest_efficiency,
        -total_time_minutes,
        -total_cost,
        -bus_time_minutes
    )


# ---------------------------------------------------------
# MAIN PLANNER
# ---------------------------------------------------------

def get_plan(
    starting_hub,
    budget,
    interests,
    max_time_minutes
):

    print()
    print("========================================")
    print("STARTING TRIP PLANNER")
    print("========================================")
    print("Starting:", starting_hub)
    print("Budget:", budget)
    print("Maximum time:", max_time_minutes)
    print("Interests:", interests)
    print()

    # -----------------------------------------------------
    # LOAD HUBS
    # -----------------------------------------------------

    hubs = fetch_hub_locations()

    if not hubs:
        return {
            "error": "Could not retrieve Ember locations."
        }

    starting_id = get_id(
        hubs,
        starting_hub
    )

    if starting_id is None:
        return {
            "error": (
                f"Could not find Ember hub for "
                f"{starting_hub}."
            )
        }

    # -----------------------------------------------------
    # LOAD ATTRACTIONS
    # -----------------------------------------------------

    attractions = load_attractions_csv()

    if not attractions:
        return {
            "error": "Could not load attractions."
        }

    selected_interests = {
        normalise_interest(interest)
        for interest in interests
    }

    print(
        "Normalised interests:",
        selected_interests
    )
    print()

    # -----------------------------------------------------
    # DESTINATIONS
    # -----------------------------------------------------

    destinations = [
        city
        for city in TARGET_CITIES
        if city.lower() != starting_hub.lower()
    ]

    # -----------------------------------------------------
    # DESTINATION HUB IDS
    # -----------------------------------------------------

    destination_ids = {}

    for destination in destinations:

        destination_id = get_id(
            hubs,
            destination
        )

        if destination_id is not None:
            destination_ids[destination] = (
                destination_id
            )

    if not destination_ids:
        return {
            "error": "Could not find any destination hubs."
        }

    # -----------------------------------------------------
    # FETCH BUS JOURNEYS
    # -----------------------------------------------------

    print("Fetching bus journeys...")
    print()

    outbound_journeys = {}
    return_journeys = {}

    for destination, destination_id in destination_ids.items():

        print(
            f"Fetching outbound: "
            f"{starting_hub} -> {destination}"
        )

        outbound_result = fetch_journeys(
            starting_id,
            destination_id
        )

        outbound_journeys.update(
            outbound_result
        )

        print(
            f"Fetching return: "
            f"{destination} -> {starting_hub}"
        )

        return_result = fetch_journeys(
            destination_id,
            starting_id
        )

        return_journeys.update(
            return_result
        )

    # Prepare the journey data once.
    prepared_outbound = prepare_journeys(
        outbound_journeys
    )

    prepared_return = prepare_journeys(
        return_journeys
    )

    # -----------------------------------------------------
    # CURRENT TIME
    # -----------------------------------------------------

    now = datetime.now().astimezone()

    all_trips = []

    # -----------------------------------------------------
    # PROCESS EACH DESTINATION
    # -----------------------------------------------------

    for destination, destination_id in destination_ids.items():

        print()
        print("----------------------------------------")
        print("DESTINATION:", destination)
        print("----------------------------------------")

        # -------------------------------------------------
        # OUTBOUND BUS
        # -------------------------------------------------

        outbound_bus = get_next_journey(
            prepared_outbound,
            starting_id,
            destination_id,
            now
        )

        if outbound_bus is None:
            print(
                "No outbound bus available."
            )
            continue

        outbound_departure = parse_datetime(
            outbound_bus["departure_time"]
        )

        outbound_arrival = parse_datetime(
            outbound_bus["arrival_time"]
        )

        outbound_duration = (
            outbound_bus["duration_minutes"]
        )

        outbound_cost = (
            outbound_bus["cost"]
        )

        print(
            "Outbound:",
            outbound_departure,
            "->",
            outbound_arrival
        )

        # -------------------------------------------------
        # DESTINATION ATTRACTIONS
        # -------------------------------------------------

        destination_attractions = [
            attraction
            for attraction in attractions
            if attraction["city"].lower()
            == destination.lower()
        ]

        # Only attractions which match at least one
        # selected interest are considered.
        relevant_attractions = []

        for attraction in destination_attractions:

            attraction_interests = {
                normalise_interest(interest)
                for interest
                in attraction["interest"].split(",")
            }

            if attraction_interests.intersection(
                selected_interests
            ):
                relevant_attractions.append(
                    attraction
                )

        print(
            "Relevant attractions:",
            len(relevant_attractions)
        )

        if not relevant_attractions:
            print(
                "No attractions match the "
                "selected interests."
            )
            continue

        # -------------------------------------------------
        # TRY EVERY POSSIBLE ROUTE
        # -------------------------------------------------

        destination_trips = []

        number_of_relevant_attractions = (
            len(relevant_attractions)
        )

        for number_of_attractions in range(
            1,
            number_of_relevant_attractions + 1
        ):

            for attraction_order in permutations(
                relevant_attractions,
                number_of_attractions
            ):

                attraction_order = list(
                    attraction_order
                )

                # -----------------------------------------
                # WALKING
                # -----------------------------------------

                walking_time, walking_distance = (
                    calculate_attraction_route(
                        attraction_order
                    )
                )

                # -----------------------------------------
                # ATTRACTION TIME
                # -----------------------------------------

                attraction_time = sum(
                    attraction[
                        "duration_minutes"
                    ]
                    for attraction
                    in attraction_order
                )

                # -----------------------------------------
                # ATTRACTION COST
                # -----------------------------------------

                attraction_cost = sum(
                    attraction["cost"]
                    for attraction
                    in attraction_order
                )

                # -----------------------------------------
                # FINISH TIME AT ATTRACTIONS
                # -----------------------------------------

                activity_end = (
                    outbound_arrival
                    + timedelta(
                        minutes=(
                            attraction_time
                            + walking_time
                        )
                    )
                )

                # -----------------------------------------
                # RETURN BUS
                # -----------------------------------------

                return_bus = get_next_journey(
                    prepared_return,
                    destination_id,
                    starting_id,
                    activity_end
                )

                if return_bus is None:
                    continue

                return_departure = parse_datetime(
                    return_bus["departure_time"]
                )

                return_arrival = parse_datetime(
                    return_bus["arrival_time"]
                )

                return_duration = (
                    return_bus["duration_minutes"]
                )

                return_cost = (
                    return_bus["cost"]
                )

                # -----------------------------------------
                # TOTAL BUS TIME
                # -----------------------------------------

                total_bus_time = (
                    outbound_duration
                    + return_duration
                )

                # -----------------------------------------
                # TOTAL BUS COST
                # -----------------------------------------

                total_bus_cost = (
                    outbound_cost
                    + return_cost
                )

                # -----------------------------------------
                # TOTAL TRIP TIME
                # -----------------------------------------

                total_time = (
                    (
                        return_arrival
                        - outbound_departure
                    ).total_seconds()
                    / 60
                )

                # -----------------------------------------
                # TOTAL TRIP COST
                # -----------------------------------------

                total_cost = (
                    total_bus_cost
                    + attraction_cost
                )

                # -----------------------------------------
                # CHECK CONSTRAINTS
                # -----------------------------------------

                if total_time > max_time_minutes:
                    continue

                if total_cost > budget:
                    continue

                # -----------------------------------------
                # MATCHED INTERESTS
                # -----------------------------------------

                covered_interests = set()

                for attraction in attraction_order:

                    attraction_interests = {
                        normalise_interest(interest)
                        for interest
                        in attraction[
                            "interest"
                        ].split(",")
                    }

                    covered_interests.update(
                        attraction_interests.intersection(
                            selected_interests
                        )
                    )

                matched_attraction_count = len(
                    attraction_order
                )

                distinct_interest_count = len(
                    covered_interests
                )

                if total_time > 0:
                    interest_efficiency = (
                        matched_attraction_count
                        / total_time
                    )
                else:
                    interest_efficiency = 0

                # -----------------------------------------
                # SCORE
                # -----------------------------------------

                score = calculate_trip_score(
                    attraction_order,
                    selected_interests,
                    total_time,
                    total_cost,
                    total_bus_time
                )

                # -----------------------------------------
                # STORE TRIP
                # -----------------------------------------

                trip = {
                    "destination": destination,

                    "attractions": attraction_order,

                    "matched_interests": sorted(
                        covered_interests
                    ),

                    "relevant_attraction_count":
                        matched_attraction_count,

                    "distinct_interest_count":
                        distinct_interest_count,

                    "interest_efficiency":
                        interest_efficiency,

                    "outbound": {
                        "departure":
                            outbound_bus[
                                "departure_time"
                            ],
                        "arrival":
                            outbound_bus[
                                "arrival_time"
                            ],
                        "duration_minutes":
                            outbound_duration,
                        "cost":
                            outbound_cost
                    },

                    "return": {
                        "departure":
                            return_bus[
                                "departure_time"
                            ],
                        "arrival":
                            return_bus[
                                "arrival_time"
                            ],
                        "duration_minutes":
                            return_duration,
                        "cost":
                            return_cost
                    },

                    "walking_time_minutes":
                        walking_time,

                    "walking_distance_km":
                        walking_distance,

                    "attraction_time_minutes":
                        attraction_time,

                    "attraction_cost":
                        attraction_cost,

                    "bus_time_minutes":
                        total_bus_time,

                    "bus_cost":
                        total_bus_cost,

                    "total_time_minutes":
                        total_time,

                    "total_cost":
                        total_cost,

                    "score":
                        score
                }

                destination_trips.append(
                    trip
                )

        # -------------------------------------------------
        # BEST TRIP FOR DESTINATION
        # -------------------------------------------------

        if not destination_trips:
            print(
                "No valid trips for",
                destination
            )
            continue

        destination_trips.sort(
            key=lambda trip: trip["score"],
            reverse=True
        )

        best_trip = destination_trips[0]

        print()
        print(
            "BEST ROUTE:",
            destination
        )

        print(
            "Attractions:",
            [
                attraction["name"]
                for attraction
                in best_trip["attractions"]
            ]
        )

        print(
            "Matched interests:",
            best_trip[
                "matched_interests"
            ]
        )

        print(
            "Relevant attractions:",
            best_trip[
                "relevant_attraction_count"
            ]
        )

        print(
            "Total time:",
            round(
                best_trip[
                    "total_time_minutes"
                ],
                1
            ),
            "minutes"
        )

        print(
            "Total cost: £",
            round(
                best_trip["total_cost"],
                2
            )
        )

        all_trips.append(
            best_trip
        )

    # -----------------------------------------------------
    # GLOBAL TRIP RANKING
    # -----------------------------------------------------

    if not all_trips:
        return {
            "error": (
                "No valid trips could be found "
                "within the selected constraints."
            )
        }

    all_trips.sort(
        key=lambda trip: trip["score"],
        reverse=True
    )

    print()
    print("========================================")
    print("TRIP RANKING")
    print("========================================")

    for index, trip in enumerate(
        all_trips,
        start=1
    ):

        print(
            index,
            trip["destination"],
            "| attractions:",
            trip[
                "relevant_attraction_count"
            ],
            "| interests:",
            trip[
                "distinct_interest_count"
            ],
            "| time:",
            round(
                trip[
                    "total_time_minutes"
                ],
                1
            ),
            "min | cost: £",
            round(
                trip["total_cost"],
                2
            )
        )

    # -----------------------------------------------------
    # FRONTEND ROUTE
    # -----------------------------------------------------

    best_trip = all_trips[0]

    route = [
        {
            "type": "start",
            "name": starting_hub
        }
    ]

    for attraction in best_trip["attractions"]:

        route.append({
            "type": "attraction",
            "name": attraction["name"],
            "city": attraction["city"],
            "lat": attraction["lat"],
            "lon": attraction["lon"],
            "duration_minutes":
                attraction["duration_minutes"],
            "cost":
                attraction["cost"],
            "interests":
                attraction["interest"]
        })

    route.append({
        "type": "return",
        "name": starting_hub
    })

    # -----------------------------------------------------
    # FINAL RESULT
    # -----------------------------------------------------

    return {
        "route": route,
        "trips": all_trips
    }