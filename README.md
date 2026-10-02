# Ember_Adventure-WICS_Hackathon_2026

## Plan

- The plan is broken into 4 parts (parsing the API, turning data into trips, the frontend and AI integration / Map)
- Person 1 should start on the API calls and tell person 2 what the format is
- Person 2 should start on importing the CSV and storing all of its information
- Person 3 and 4 should start with the initial fill-in form of the website


1 (API -> Data):

Need to make functions which send a request to the API
Need to then get the JSON data from the API and turn it into python code
Should likely be stored as list of journeys with departure, arrival, time, duration and cost
Should make function where, when provided a given time, origin and destination, the next bus is found
Import CSV of attractions into code and make sure tha information is also stored
After this is finished can take some of the workload off of (2)

2 (Data -> Trips):

!!! Most important part

Each attraction has an interest, cost and duration
You would first need to get the time taken for a bus 

Algorithm for choosing destinations:

for every possible stop from the starting stops within {Edinburgh, Glasgow, Dundee, Aberdeen, Perth}
    find next trip to that location and subtracts its time and cost from the total
    find all attractions for the location
    use Haversine formula to calculate walking distances between consecutive attractions in each potential route
    use algorithm for picking best route
    store all of the info about attractions and route times etc (to be fed to the AI later)
Score all trips and put in order to be sent to front end

Algorithm for picking best route for a destination:

First make sure addition to route leaves you with enough money for bus back
Calculate interest per minute: (how many interest the current route does out of all selected interests) / (total time taken (everything that takes time))

Algorithm for scoring all trips:

1: Interest match: how many of the listed interests where met (Eg if interests are History and Food and there is only Food on the trip, give 1/2)
2: Time Efficiency: Trips with the same interest score but which took less time are sorted higher
3: Cost Efficiency: If two trips had the same score and time, rank by cost
4: Travel Efficiency: Trips with the same score, time and cost are then ranked by how long the bus journey took

3 (Frontend):

Create form for user to enter start position, time, money and any interests they have and send input to vackend
Display loading screen while route is calculated (right after data is sent)
Create a display for the itinerary (most likely in the form of cards that the user can swipe away with relevant info on them) (you have quite a lot of creative liberty with the visuals just make sure it looks good)
Handle when there are no trips
DO CSS near the end (need it to work first)
When done work on (2)

4 (Additional features):
Can either start by focussing on getting the AI to work or by helping (2)

Send the itinerary to an AI which will provide a 'unique description' of the trip (make sure walking times is an 'estimated walking time' bc it's a straight line between both locations).
Will expect to have latitute / longitude values for every bus stop and attraction
Would need to plot these on a map of Scotland with their location names and have that information on the HTML page.
Don't initially bother about having lines between each location as they're calculated as straight lines to save time


Additional features:

- A suprise me feature which randomly generates a trip that lines up with the users preferences