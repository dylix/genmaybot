import requests
import datetime
import math
import sys
from math import cos, asin, sqrt

error_msg = "Could not retrieve current air quality data."
json_error_msg = "JSON schema in response has changed. Please fix me. Key error: {}"
location_missing_msg = "Use !setstation <stationid> to save your station id to the bot. Find your stationID at https://www.purpleair.com/map?mylocation or alternatively use !aqi <zipcode>"

def get_stationid(self, lat, lng):
    try:
        startlatlng = [float(lat), float(lng)]
        station_list = getPurpleAirList()
        closest_station = closest(station_list['data'], startlatlng)[0]
        return closest_station
    except:
        return None
    #aqi_json = getWebOutsideAqi(closest_station)
    #print(aqi_json)

def getWebOutsideAqi(station_id):
    USER_AGENT = f"airqualityBot/v1 (https://dylix.org)"
    HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    response = requests.get(f"https://dylix.org/aqiJson?id={station_id}", headers=HEADERS) #137368
    return response.json()

def closest(data, v):
    return min(data, key=lambda p: distance(v[0],v[1],p[1],p[2]))

def distance(lat1, lon1, lat2, lon2):
    if lat2 is None or lon2 is None:
        return 10000000
    p = 0.017453292519943295
    hav = 0.5 - cos((lat2-lat1)*p)/2 + cos(lat1*p)*cos(lat2*p) * (1-cos((lon2-lon1)*p)) / 2
    return 12742 * asin(sqrt(hav))

def getPurpleAirList():
    USER_AGENT = f"airqualityBot/v1 (https://dylix.org)"
    HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json", "X-API-Key": "CCF6ADE0-0747-11EC-BAD6-42010A800017"}
    response = requests.get(f"https://api.purpleair.com/v1/sensors?fields=latitude,longitude&location_type=0", headers=HEADERS)
    return response.json()

def get_purpleair(self, botevent, cigs=False, dylix=False):
    stationid = ""
    try:
        if dylix:
            try:
                stationid = sys.modules['botmodules.userlocation'].get_station("dylix")
            except Exception as ex:
                pass
        else:
            stationid = botevent.input if botevent.input else botevent.user_station
            if stationid.isdigit() is False:
                address, lat, lng, country = self.tools['findLatLong'](stationid)
                stationid = get_stationid(self, lat, lng)
    except AttributeError:
        pass
    if not stationid:
        botevent.output = location_missing_msg
        return botevent

    try:
        api_key = self.botconfig["APIkeys"]["purpleAPIkey"]
    except KeyError as error:
        self.logger.error(f"purpleair API key not set. Key not found: {error}")
        return botevent

    date_format = "%Y-%m-%d"
    today = datetime.datetime.today().strftime(date_format)
    tomorrow = (datetime.datetime.today() + datetime.timedelta(days=+1)).strftime(date_format)

    purpleair_url = f"https://api.purpleair.com/v1/sensors/{stationid}"
    #purpleair_url = "https://dylix.org/pa.json"
    pa_response = []

    try:
        USER_AGENT = f"airqualityBot/v1 (https://dylix.org)"
        HEADERS = {"User-Agent": USER_AGENT, "Accept": "application/json", "X-API-Key": f"{api_key}"}
        pa_response = requests.get(purpleair_url, headers=HEADERS).json()
    except Exception:
        self.logger.exception(error_msg)
        botevent.output = error_msg

    if not pa_response:
        botevent.output = error_msg
        return botevent

    calculated_aqi = ""
    sensor_pm = ""
    sensor_name = ""
    sensor_temp = ""
    sensor_lastseen = ""

    try:
        sensor_pm = pa_response['sensor']['pm2.5']
        sensor_name = pa_response['sensor']['name']
        sensor_temp = f"Temp: {pa_response['sensor']['temperature']}°F / "
        sensor_lastseen = datetime.datetime.fromtimestamp(pa_response['sensor']['last_seen'])
        sensor_lastseen = (datetime.datetime.now() - sensor_lastseen).total_seconds() / 60
        sensor_lastseen = round(int(sensor_lastseen),0)
        calculated_aqi = calcAQIpm25(sensor_pm)
    except KeyError as error:
        botevent.output = f"{json_error_msg.format(error)}"
        return botevent
    if cigs:
        cigs_per_day = calc_cigs_day(sensor_pm)
        cigs_per_hour = cigs_per_day / 24
        cigs_per_hour_exercise = cigs_per_hour * 20
        botevent.output = f"24 hours in AQI {calculated_aqi} ({sensor_pm}-ug/m3) is equal to {round(cigs_per_day,2)} cigarettes a day. Exercising? 1hour={round(cigs_per_hour_exercise,2)} cigs | 2hours={round((cigs_per_hour_exercise * 2),2)} cigs | 3hours={round((cigs_per_hour_exercise * 3),2)} cigs | 4hours={round((cigs_per_hour_exercise * 4),2)} cigs | Sensor: {stationid}"
    else:
        botevent.output = f"AQI: {calculated_aqi} / PM2.5-ug/m3: {sensor_pm} / {sensor_temp} Name: {sensor_name} / Sensor: {stationid} / Updated: {sensor_lastseen} mins ago"
    return botevent

get_purpleair.command = "!pa"
get_purpleair.helptext = "Usage: !pa <stationid> Retrieves air quality info from purpleair.com"

def get_cigs(self, e):
    return get_purpleair(self, e, True)
get_cigs.command = "!cigs"
get_cigs.helptext = "Usage: !cigs <stationid> Retrieves air quality info from purpleair.com and then calculates equivalent cigarettes using DYLIX math."

def calc_cigs_day(pm25):
    return float(pm25/22)

def calcAQIpm25(pm25):
    pm1 = 0
    pm2 = 12
    pm3 = 35.4
    pm4 = 55.4
    pm5 = 150.4
    pm6 = 250.4
    pm7 = 350.4
    pm8 = 500.4
    aqi1 = 0
    aqi2 = 50
    aqi3 = 100
    aqi4 = 150
    aqi5 = 200
    aqi6 = 300
    aqi7 = 400
    aqi8 = 500
    aqipm25 = 0
    pm25 = round(10 * pm25) / 10
    if pm25 >= pm1 and pm25 <= pm2:
        aqipm25 = ((aqi2 - aqi1) / (pm2 - pm1)) * (pm25 - pm1) + aqi1
    elif pm25 >= pm2 and pm25 <= pm3:
        aqipm25 = ((aqi3 - aqi2) / (pm3 - pm2)) * (pm25 - pm2) + aqi2
    elif pm25 >= pm3 and pm25 <= pm4:
        aqipm25 = ((aqi4 - aqi3) / (pm4 - pm3)) * (pm25 - pm3) + aqi3
    elif pm25 >= pm4 and pm25 <= pm5:
        aqipm25 = ((aqi5 - aqi4) / (pm5 - pm4)) * (pm25 - pm4) + aqi4
    elif pm25 >= pm5 and pm25 <= pm6:
        aqipm25 = ((aqi6 - aqi5) / (pm6 - pm5)) * (pm25 - pm5) + aqi5
    elif pm25 >= pm6 and pm25 <= pm7:
        aqipm25 = ((aqi7 - aqi6) / (pm7 - pm6)) * (pm25 - pm6) + aqi6
    elif pm25 >= pm7 and pm25 <= pm8:
        aqipm25 = ((aqi8 - aqi7) / (pm8 - pm7)) * (pm25 - pm7) + aqi7
    else:
        return 501
    return int(aqipm25)
    
def calcAQIpm10(pm10):
    pm1 = 0
    pm2 = 54
    pm3 = 154
    pm4 = 254
    pm5 = 354
    pm6 = 424
    pm7 = 504
    pm8 = 604
    aqi1 = 0
    aqi2 = 50
    aqi3 = 100
    aqi4 = 150
    aqi5 = 200
    aqi6 = 300
    aqi7 = 400
    aqi8 = 500
    aqipm10 = 0
    if pm10 >= pm1 and pm10 <= pm2:
        aqipm10 = ((aqi2 - aqi1) / (pm2 - pm1)) * (pm10 - pm1) + aqi1
    elif pm10 >= pm2 and pm10 <= pm3:
        aqipm10 = ((aqi3 - aqi2) / (pm3 - pm2)) * (pm10 - pm2) + aqi2
    elif pm10 >= pm3 and pm10 <= pm4:
        aqipm10 = ((aqi4 - aqi3) / (pm4 - pm3)) * (pm10 - pm3) + aqi3
    elif pm10 >= pm4 and pm10 <= pm5:
        aqipm10 = ((aqi5 - aqi4) / (pm5 - pm4)) * (pm10 - pm4) + aqi4
    elif pm10 >= pm5 and pm10 <= pm6:
        aqipm10 = ((aqi6 - aqi5) / (pm6 - pm5)) * (pm10 - pm5) + aqi5
    elif pm10 >= pm6 and pm10 <= pm7:
        aqipm10 = ((aqi7 - aqi6) / (pm7 - pm6)) * (pm10 - pm6) + aqi6
    elif pm10 >= pm7 and pm10 <= pm8:
        aqipm10 = ((aqi8 - aqi7) / (pm8 - pm7)) * (pm10 - pm7) + aqi7
    return int(aqipm10)