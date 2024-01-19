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
    #print('using test json')
    #url = f"https://dylix.org/testfire.json"
    try:
        fire_json = request_json(url)
        combined_fire_info = 'Biggest 3: '
        fire_num = 1
        #for fire in fire_json['data']['features']:
        features = fire_json['data']['features']
        fire_json_sorted = sorted(features, key=lambda k: k['properties'].get('acres', 0), reverse=True)
        for fire in fire_json_sorted:
            #top3
            if fire_num > 3:
                break
            fire_contained = fire['properties']['percent_contained'] or 'Unknown'
            combined_fire_info += f"#{fire_num} {fire['properties']['name']} / Acres:{fire['properties']['acres']} / {fire_contained}% Contained / Discovered {fire['properties']['firediscov']} / Cause: {fire['properties']['firecause']} | ";
            fire_num += 1
        e.output = combined_fire_info[:455]
        #purpleair_output = self.bangcommands["!pa"](self, e, False, True)
        #e.output = f"OUTSIDE / {purpleair_output.output}\nINSIDE / AQI: {purpleair.calcAQIpm25(int(float(room_aqi['pm25'])))} [PM2.5->({room_aqi['pm25']}µg/m3)] / {purpleair.calcAQIpm10(int(float(room_aqi['pm10'])))} [PM10->({room_aqi['pm10']}µg/m3)] / Temp: {room_temp['temp']}°F / Humidity: {room_temp['humidity']}% / HR: {hr['hr']}bpm / Updated: {hr['time'].split(' ')[1][:5]}";
        #print()
        #e.output = f"INSIDE / AQI: {purpleair.calcAQIpm25(int(float(room_aqi['pm25'])))} [PM2.5->({room_aqi['pm25']}µg/m3)] / {purpleair.calcAQIpm10(int(float(room_aqi['pm10'])))} [PM10->({room_aqi['pm10']}µg/m3)] / Temp: {room_temp['temp']}°F / Humidity: {room_temp['humidity']}% / HR: {hr['hr']}bpm / Updated: {hr['time'].split(' ')[1][:5]}";
    except Exception as ex:
        print(ex)
        pass
    return e

def request_json(url):
    #headers = {'Authorization': 'access_token ' + request_json.token}
    # print ("Strava: requesting %s Headers: %s" % (url, headers))
    headers = {}
    req = urllib.request.Request(url, None, headers)
    response = urllib.request.urlopen(req)
    try:
        response = json.loads(response.read().decode('utf-8'))
    except:
        response = json.loads(response.read())
    return response