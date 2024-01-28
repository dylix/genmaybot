import json, urllib.request, urllib.error, urllib.parse, re, botmodules.purpleair as purpleair
import ast
try:
    import botmodules.userlocation as user
except ImportError:
    user = None

def get_fire(self, e):
    try:
        location = e.location
    except:
        location = e.input
    if location and user.get_location(location):
        location = user.get_location(location) #allow looking up by nickname
    if location == "" and user:
        location = user.get_location(e.nick)
    get_fire_info(self, e, location)
    return e
get_fire.command = "!fire"
get_fire.helptext = "!fire - gets relatively close fire information to your area"

def get_fire_info(self, e, location=""):
    if location == "":
        location = e.input
    if location == "" and user:
        location = user.get_location(e.nick)
    try:
        address, lat, lng, country = self.tools['findLatLong'](location)
    except:
        e.output = "No location was found"
        return e
    url = f"https://api.weatherusa.net/v1/fire?q={lat},{lng}&radius=160934&acres=20&perimeters=false";
    try:
        fire_json = request_json(url)
        features = fire_json['data']['features']
        num_fires = len(features)
        if num_fires >= 3:
            combined_fire_info = f'# of fires: {num_fires} | Listing biggest {top_fires} | '
        else:
            combined_fire_info = f'# of fires: {num_fires} | '

        fire_num = 1
        fire_json_sorted = sorted(features, key=lambda k: k['properties'].get('acres', 0), reverse=True)
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