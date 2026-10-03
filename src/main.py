
def chooseDestinations(startingHub, cost, duration, interests):

    #Get map of location name to id, lat and long
    stops = fetch_hub_locations()
    starting_id = stops[startingHub]["id]"]

    for (stop in stops):
        destination_id = stop["id"]
        journeys = fetch_journeys(starting_id, destination_id)
        get_next_bus(journeys, starting_id, destination_id, current_time_str):

