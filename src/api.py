import requests

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
