import json, urllib.request, urllib.error, urllib.parse, re, requests, botmodules.purpleair as purpleair

def dylix(self, e):
    hr = request_json("https://dylix.org/db2json?db=heartrate&limit=1")[0]
    room_temp = request_json("https://dylix.org/db2json?db=roomtemp&limit=1")[0]
    room_aqi = request_json("https://dylix.org/db2json?db=aqi&limit=1")[0]
    try:
        purpleair_output = self.bangcommands["!pa"](self, e, False, True)
        e.output = f"OUTSIDE / {purpleair_output.output}\nINSIDE / AQI: {purpleair.calcAQIpm25(int(float(room_aqi['pm25'])))} [PM2.5->({room_aqi['pm25']}µg/m3)] / {purpleair.calcAQIpm10(int(float(room_aqi['pm10'])))} [PM10->({room_aqi['pm10']}µg/m3)] / Temp: {room_temp['temp']}°F / Humidity: {room_temp['humidity']}% / HR: {hr['hr']}bpm / Updated: {hr['time'].split(' ')[1][:5]}";
        #print()
        #e.output = f"INSIDE / AQI: {purpleair.calcAQIpm25(int(float(room_aqi['pm25'])))} [PM2.5->({room_aqi['pm25']}µg/m3)] / {purpleair.calcAQIpm10(int(float(room_aqi['pm10'])))} [PM10->({room_aqi['pm10']}µg/m3)] / Temp: {room_temp['temp']}°F / Humidity: {room_temp['humidity']}% / HR: {hr['hr']}bpm / Updated: {hr['time'].split(' ')[1][:5]}";
    except:
        pass
    return e

dylix.command = "!dylix"
dylix.helptext = "!dylix - gets dylix's hr and airquality from inside/outside"

def dylix_hr(self, e):
    hr = request_json("https://dylix.org/db2json?db=heartrate&limit=1")[0]
    try:
        e.output = f"dylix's HR: {hr['hr']}bpm / RR Int: {hr['rr']} / Updated: {hr['time'].split(' ')[1][:5]}";
    except:
        pass
    return e
dylix_hr.command = "!hr"
dylix_hr.helptext = "!hr - gets dylix's hr"

def request_json(url):
    #headers = {'Authorization': 'access_token ' + request_json.token}
    # print ("Strava: requesting %s Headers: %s" % (url, headers))
    headers = {}
    req = urllib.request.Request(url, None, headers)
    response = urllib.request.urlopen(req)
    response = json.loads(response.read().decode('utf-8'))
    return response

def getWebDadJoke(self, e):
    USER_AGENT = f"jokebot/v1 (https://dylix.org)"
    HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    try:
        response = requests.get("https://icanhazdadjoke.com/", headers=HEADERS)
        e.output = response.json()["joke"]
    except:
        pass
    return e
getWebDadJoke.command = "!joke"
getWebDadJoke.helptext = "!joke - gets a random dad joke"

def frisco(self, e):
    try:
        e.output = f"Theme song: https://www.youtube.com/watch?v=saJ80UKo1YU";
    except:
        pass
    return e

frisco.command = "!frisco"
frisco.helptext = ""

def frisko(self, e):
    return frisco(self,e)

frisko.command = "!frisko"
frisko.helptext = ""