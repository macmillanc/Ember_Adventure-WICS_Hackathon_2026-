import requests
from datetime import datetime


#RUNS WITH /usr/local/python/bin/python3.13 api.py

def fetch_hub_locations():
    """
    Fetches all Ember bus stops and filters for the main hubs 
    needed by Person 2 (Edinburgh, Glasgow, Dundee, Aberdeen, Perth).
    """
    url = "https://api.ember.to/v1/locations/"
    
    # We want STOP_AREAs (the general stations) rather than every individual stance
    params = {"type": "STOP_AREA"} 
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    all_locations = response.json()
    
    target_cities = ["Edinburgh", "Glasgow", "Dundee", "Aberdeen", "Perth"]
    hubs = {}
    
    for loc in all_locations:
        # Check if the location name contains any of our target cities
        if any(city in loc.get("name", "") for city in target_cities):
            hubs[loc["name"]] = {
                "id": loc["id"],
                "lat": loc.get("lat"), 
                "lon": loc.get("lon")
            }
            
    return hubs

def get_next_bus(journeys, origin, destination, current_time_str):
    """
    Finds the next available bus after a given time.
    """
    current_time = datetime.fromisoformat(current_time_str)
    valid_options = []
    
    for j in journeys:
        if j["origin"] == origin and j["destination"] == destination:
            dep_time = datetime.fromisoformat(j["departure_time"])
            if dep_time >= current_time:
                valid_options.append(j)
                
    if not valid_options:
        return None
        
    valid_options.sort(key=lambda x: x["departure_time"])
    return valid_options[0]

if __name__ == "__main__":
    print("--- TEST 1: Fetching Live Hub Locations ---")
    try:
        hubs = fetch_hub_locations()
        print(f"Successfully loaded {len(hubs)} hubs:")
        for name, data in hubs.items():
            print(f" - {name}: ID={data['id']}, Lat={data['lat']}, Lon={data['lon']}")
    except Exception as e:
        print(f"Failed to fetch hubs: {e}")

    print("\n--- TEST 2: Testing Next Bus Logic (Dummy Data) ---")
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
        journeys=dummy_journeys, 
        origin="Edinburgh", 
        destination="Glasgow", 
        current_time_str="2026-10-03T11:00:00"
    )
    
    if next_bus:
        print(f"Next bus found! Leaves at {next_bus['departure_time']} and costs £{next_bus['cost']}")
    else:
        print("No upcoming buses found.")