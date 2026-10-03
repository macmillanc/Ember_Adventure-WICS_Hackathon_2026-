import csv
from datetime import datetime, date
from pathlib import Path
import requests

# RUNS WITH /usr/local/python/bin/python3.13 api.py

# CONSTANTS
API_BASE_URL = "https://api.ember.to/v1"
TARGET_CITIES = ["Edinburgh", "Glasgow", "Dundee", "Aberdeen", "Perth"]



#RETURNS:
# hubs The id, the lat and longitude 
def fetch_hub_locations():
    """
    Fetches all Ember bus stops and filters for the main hubs 
    needed by Person 2 (Edinburgh, Glasgow, Dundee, Aberdeen, Perth).
    """
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
    response.raise_for_status()
    all_locations = response.json()
    
    hubs = {}
    for loc in all_locations:
        name = loc.get("name", "")
        # Only process exact matches present in your hardcoded dictionary
        if name in hardcoded_coords:
            hubs[name] = {
                "id": loc["id"],
                "lat": hardcoded_coords[name]["lat"],
                "lon": hardcoded_coords[name]["lon"],
            }
            
    return hubs
#returns id based on the location given

def get_id(hubs, location):
    for name, data in hubs.items():
        if location.lower() in name.lower() and "city centre" in name.lower():
            return data["id"]
    for name, data in hubs.items():
            if location.lower() in name.lower():
                return data["id"]
    return None




#returns a dictionary

# the keys are the origin id and destination id
# the values in the dictionary are departure time, arrival time , duration in minutes and cost
def fetch_journeys(origin_id, destination_id):
    """
    Fetches available quotes/journeys between two hub IDs for a given date.
    Returns a standardized dictionary map record.
    """

    travel_date = date.today().isoformat()
        
    url = f"{API_BASE_URL}/quotes/"
    params = {
        "origin": origin_id,
        "destination": destination_id,
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
def load_attractions_csv(filepath=None):
    """
    Loads attractions from the CSV file using the correct column headers:
    id, destination, attraction, interests, cost_gbp, duration_minutes, latitude, longitude
    """
    if filepath is None:
        script_dir = Path(__file__).resolve().parent
        filepath = script_dir.parent / "data" / "attractions.csv"
    
    attractions = []
    
    try:
        with open(filepath, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                attractions.append({
                    "name": row["attraction"],
                    "city": row["destination"],
                    "interest": row["interests"].lower(),
                    "cost": float(row["cost_gbp"]),
                    "duration_minutes": int(row["duration_minutes"]),
                    "lat": float(row["latitude"]),
                    "lon": float(row["longitude"])
                })
        print(f"Successfully loaded {len(attractions)} attractions from {filepath}.")
    except FileNotFoundError:
        print(f"ERROR: Could not find attractions.csv at: {filepath}")
    except KeyError as e:
        print(f"ERROR: Missing expected column in CSV: {e}")
        
    return attractions


#Returns the departure time, minutes and cost

def get_next_bus(journeys_data, origin_id, destination_id, current_time_str):
    """
    Finds the next available bus after a given time.
    Supports both dictionary maps (tuple keys) and flat journey lists.
    """
    current_time = datetime.fromisoformat(current_time_str)
    
    # Handle both map structure and legacy list structure smoothly
    if isinstance(journeys_data, dict):
        route_key = (origin_id, destination_id)
        journey_list = journeys_data.get(route_key, [])
    else:
        journey_list = [
            j for j in journeys_data 
            if j.get("origin") == origin_id and j.get("destination") == destination_id
        ]
    
    valid_options = []
    for j in journey_list:
        dep_time = datetime.fromisoformat(j["departure_time"])
        if dep_time >= current_time:
            valid_options.append(j)
            
    if not valid_options:
        return None
        
    valid_options.sort(key=lambda x: x["departure_time"])
    return valid_options[0]











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
    )
    
    if next_bus:
        print(f"Next bus found! Leaves at {next_bus['departure_time']} and costs £{next_bus['cost']}")
    else:
        print("No upcoming buses found.")


    print("id is:")
    print(get_id(fetch_hub_locations(), "Aberdeen"))