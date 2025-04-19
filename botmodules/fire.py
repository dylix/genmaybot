import json, urllib.request, urllib.error, urllib.parse, re, botmodules.purpleair as purpleair
import ast
import math

try:
    import botmodules.userlocation as user
except ImportError:
    user = None

def closest(data, v):
    return min(data, key=lambda p: distance(v[0],v[1],p[1],p[2]))

def distance(lat1, lon1, lat2, lon2):
    if lat2 is None or lon2 is None:
        return 10000000
    p = 0.017453292519943295
    hav = 0.5 - math.cos((lat2-lat1)*p)/2 + math.cos(lat1*p)*math.cos(lat2*p) * (1-math.cos((lon2-lon1)*p)) / 2
    return 12742 * math.asin(math.sqrt(hav))

def get_fire(self, e):
    close = False
    myInput = str(e.input)
    if "close" in myInput or "closest" in myInput:
        myInput = str(e.input).strip().replace("close","").strip()
        myInput = str(e.input).strip().replace("closest","").strip()
        close = True
    try:
        location = e.location
    except:
        location = myInput #e.input
    if location and user.get_location(location):
        location = user.get_location(location) #allow looking up by nickname
    if location == "" and user:
        location = user.get_location(e.nick)
    get_fire_info(self, e, location, myInput, close)
    return e
get_fire.command = "!fire"
get_fire.helptext = "!fire - gets relatively close fire information to your area"

def get_fire_info(self, e, location="", myInput="", close = False):
    if location == "":
        location = myInput#e.input
    if location == "" and user:
        location = user.get_location(e.nick)
    try:
        address, lat, lng, country = self.tools['findLatLong'](location)
    except:
        e.output = "No location was found"
        return e
    url = f"https://api.weatherusa.net/v1/fire?q={lat},{lng}&radius=321868&acres=20&perimeters=false";
    #url = f"https://dylix.org/test2.json"

    try:
        fire_json = request_json(url)
        features = fire_json['data']['features']
        num_fires = len(features)
        top_fires = 3
        if close:
            if num_fires >= 3:
                combined_fire_info = f'# of fires: {num_fires} | Listing closest {top_fires} | '
            else:
                combined_fire_info = f'# of fires: {num_fires} | '
        else:
            if num_fires >= 3:
                combined_fire_info = f'# of fires: {num_fires} | Listing biggest {top_fires} | '
            else:
                combined_fire_info = f'# of fires: {num_fires} | '

        combined_fire_info += f'Radius 200 miles from {address} | '
        
        fire_num = 1
        if close:
            #fire_json_sorted = sorted(features, key=lambda k: int(k['properties'].get('acres', 0)), reverse=True)
            fire_json_sorted = sorted(features, key= lambda d: distance(d['geometry']['coordinates'][1], d['geometry']['coordinates'][0], lat, lng), reverse=False)
        else:
            fire_json_sorted = sorted(features, key=lambda k: int(k['properties'].get('acres', 0)), reverse=True)
        for fire in fire_json_sorted:
            if fire_num > 3:
                break
            fire_contained = fire['properties']['percent_contained'] or 'Unknown'
            combined_fire_info += f"#{fire_num} {fire['properties']['name']} / Acres:{fire['properties']['acres']} / {fire_contained}% Contained / Discovered {fire['properties']['firediscov']} / Cause: {fire['properties']['firecause']} | ";
            fire_num += 1
        e.output = self.tools['insert_at_closest_space'](combined_fire_info[:-3])
    except Exception as ex:
        print(ex)
        pass
    return e

def request_json(url):
    headers = {}
    req = urllib.request.Request(url, None, headers)
    response = urllib.request.urlopen(req)
    try:
        response = json.loads(response.read().decode('utf-8'))
    except:
        response = json.loads(response.read())
    return response