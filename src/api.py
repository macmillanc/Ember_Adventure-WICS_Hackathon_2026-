import requests
import csv
from datetime import datetime, date

# RUNS WITH /usr/local/python/bin/python3.13 api.py

def fetch_hub_locations():
    """
    Fetches all Ember bus stops and filters for the main hubs 
    needed by Person 2 (Edinburgh, Glasgow, Dundee, Aberdeen, Perth).
    """
    url = "https://api.ember.to/v1/locations/"
    params = {"type": "STOP_AREA"} 
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    all_locations = response.json()
    
    target_cities = ["Edinburgh", "Glasgow", "Dundee", "Aberdeen", "Perth"]
    hubs = {}
    
    for loc in all_locations:
        if any(city in loc.get("name", "") for city in target_cities):
            hubs[loc["name"]] = {
                "id": loc["id"],
                "lat": loc.get("lat"), 
                "lon": loc.get("lon")
            }
            
    return hubs

def fetch_journeys(origin_id, destination_id, travel_date=None):
    """
    Fetches available quotes/journeys between two hub IDs for a given date.
    Returns a standardized list of journey dictionaries.
    """
    if not travel_date:
        travel_date = date.today().isoformat()
        
    url = "https://api.ember.to/v1/quotes/"
    params = {
        "origin": origin_id,
        "destination": destination_id,
        "departure_date_from": f"{travel_date}T00:00:00",
        "departure_date_to": f"{travel_date}T23:59:59"
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()
    
    journeys = []
    # Adjust based on the actual quote structure returned by the Ember API
    for quote in data.get("quotes", []):
        journeys.append({
            "origin": origin_id,
            "destination": destination_id,
            "departure_time": quote.get("departure_time"),
            "arrival_time": quote.get("arrival_time"),
            "duration_minutes": quote.get("duration_minutes", 0),
            "cost": quote.get("total_price", 0.0) / 100.0  # converted from pence to pounds
        })
        
    return journeys

def load_attractions_csv(filepath="attractions.csv"):
    """
    Loads attractions from a CSV file and returns them as a structured list.
    Expected CSV columns: name, city, interest, cost, duration_minutes, lat, lon
    """
    attractions = []
    
    try:
        with open(filepath, mode="r", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            for row in reader:
                attractions.append({
                    "name": row["name"],
                    "city": row["city"],
                    "interest": row["interest"].lower(),
                    "cost": float(row["cost"]),
                    "duration_minutes": int(row["duration_minutes"]),
                    "lat": float(row["lat"]),
                    "lon": float(row["lon"])
                })
        print(f"Successfully loaded {len(attractions)} attractions from {filepath}.")
    except FileNotFoundError:
        print(f"Warning: {filepath} not found. Make sure 'attractions.csv' is in the same folder.")
        
    return attractions

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

    print("\n--- TEST 2: Testing Attractions CSV Loading ---")
    # Make sure you have an attractions.csv file locally to test this!
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
        journeys=dummy_journeys, 
        origin="Edinburgh", 
        destination="Glasgow", 
        current_time_str="2026-10-03T11:00:00"
    )
    
    if next_bus:
        print(f"Next bus found! Leaves at {next_bus['departure_time']} and costs £{next_bus['cost']}")
    else:
        print("No upcoming buses found.")