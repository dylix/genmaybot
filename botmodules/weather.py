# -*- coding: UTF-8 -*-
import urllib.request, urllib.parse, urllib, xml.dom.minidom
import json, time, re
import requests
import datetime
import pytz
import multiline

try:
    import botmodules.userlocation as user
except ImportError:
    user = None

#TODO.. example
# FOR WEATHER FORECASTS WHEN LONG MSGS

# Shorten the title to fit perfectly in the IRC 510-character per line limit
# To do so properly, you have to convert to utf-8 because of double-byte characters
# The protocol garbage before the real message is
# :<nick>!<realname>@<hostname> PRIVMSG <target> :
'''
maxlen = 510 - len(":{}!{}@{} PRIVMSG {} : [ {} ]".format(e.botnick,
                                                          self.realname,
                                                          self.hostname,
                                                          e.source, url))
title = title[0:maxlen]
'''

def google_geocode(self, address):
    gapikey = self.botconfig["APIkeys"]["shorturlkey"] #This uses the same Google API key as URL shortener
    address = urllib.parse.quote(address)

    url = "https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}"
    url = url.format(address, gapikey)


    try:
        request = urllib.request.Request(url, None, {'Referer': 'http://irc.00id.net'})
        response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as err:
        self.logger.exception("Exception in google_geocode:")

    try:
        results_json = json.loads(response.read().decode('utf-8'))
        status = results_json['status']

        if status != "OK":
            raise

        city, state, country, poi = "","","", ""
        
        for component in results_json['results'][0]['address_components']:
            if 'locality' in component['types']:
                city = component['long_name']
            elif 'point_of_interest' in component['types'] or 'natural_feature' in component['types']:
                poi = component['long_name']
            elif 'administrative_area_level_1' in component['types']:
                state = component['short_name']
            elif 'country' in component['types']:
                if component['short_name'] != "US":                
                    country = component['long_name']
                else:
                    country = False

        if not city:
            city = poi #if we didn't find a city, maybe there was a POI or natural feature entry, so use that instead

        if not country: #Only show the state if in the US
            country == ""
        elif country != "Canada" and city:               #We don't care about provinces outside of the US and Canada, unless the city name is empty
            state = ""

        if city:
            formatted_address = "{}{}{}".format(city,"" if not state else ", " + state,"" if not country else ", " + country)
        elif state:
            formatted_address = "{}{}".format(state,"" if not country else ", " + country)
        else:
            formatted_address = "{}".format("" if not country else country)
        
        
        lng = results_json['results'][0]['geometry']['location']['lng']
        lat = results_json['results'][0]['geometry']['location']['lat']


        
    except:
        self.logger.exception("Failed to geocode location using Google API:")

        return
    
    return formatted_address, lat, lng, country

def bearing_to_compass(bearing):
    dirs = {}        
    dirs['N'] = (348.75, 11.25)
    dirs['NNE'] = (11.25, 33.75)
    dirs['NE'] = (33.75, 56.25)
    dirs['ENE'] = (56.25, 78.75)
    dirs['E'] = (78.75, 101.25)
    dirs['ESE'] = (101.25, 122.75)
    dirs['SE'] = (123.75, 146.25)
    dirs['SSE'] = (146.25, 168.75)
    dirs['S'] = (168.75, 191.25)
    dirs['SSW'] = (191.25, 213.75)
    dirs['SW'] = (213.75, 236.25)
    dirs['WSW'] = (236.25, 258.75)
    dirs['W'] = (258.75, 281.25)
    dirs['WNW'] = (281.25, 303.75)
    dirs['NW'] = (303.75, 326.25)
    dirs['NNW'] = (326.25, 348.75)

    for direction in dirs:
        min, max = dirs[direction]
        if bearing >= min and bearing <= max:
            return direction
        elif bearing >= dirs['N'][0] or bearing <= dirs['N'][1]:
            return "N"

def fahrenheit_to_celsius(temp):
    return int(round((temp - 32)*5/9,0))

def bearing_to_arrow(bearing):
    directions = {
        "↓": (337.5, 22.5),
        "↘︎": (292.5, 337.5),
        "→": (247.5, 292.5),
        "↗︎": (202.5, 247.5),
        "↑": (157.5, 202.5),
        "↖︎": (112.5 ,157.5),
        "←": (67.5, 112.5),
        "↙︎": (22.5, 67.5)
    }
    for direction in directions:
        min, max = directions[direction]
        if bearing >= min and bearing <= max:
            return direction
        elif bearing >= directions['↓'][0] or bearing <= directions['↓'][1]:
            return '↓'

def weather_summary_to_icon(icon):
    #do we really need emojis?
    return ""
    '''icons = {
        "cloudy": "\U00002601",
        "partly-cloudy-day": "\U0001F324",
        "clear-day": "️\U00002600",
        "clear-night": "\U0001F319",
        "rain": "\U0001F327",
        "snow": "\U00002744",
        "wind": "\U0001F4A8",
        "fog": "\U0001F32B"'''
    icons = {
        "01d": "️\U00002600",
        "02d": "\U0001F324",
        "03d": "\U00002601",
        "04d": "\U00002601",
        "clear-night": "\U0001F319",
        "09d": "\U0001F327",
        "10d": "\U0001F327",
        "11d": "\U00002608",
        "13d": "\U00002744",
        "wind": "\U0001F4A8",
        "50d": "\U0001F32B",
        "01n": "️\U00002600",
        "02n": "\U0001F324",
        "03n": "\U00002601",
        "04n": "\U00002601",
        "clear-night": "\U0001F319",
        "09n": "\U0001F327",
        "10n": "\U0001F327",
        "11n": "\U00002608",
        "13n": "\U00002744",
        "wind": "\U0001F4A8",
        "50n": "\U0001F32B"
    }

    try:
        return icons[icon]
    except KeyError:

        return ""

def get_weather(self, e):
    try:
        location = e.location
    except:
        location = e.input
    
    if location and user.get_location(location):
        location = user.get_location(location) #allow looking up by nickname
    
    if location == "" and user:
        location = user.get_location(e.nick)

    # Try weather functions in order
    #forecast_io(self,  e, location)
    onecall(self, e, location)
    
    if not e.output:
        get_wwo(self, location, e)
    if not e.output:
        return get_weather2(self, e)
        
    return e

get_weather.waitfor_callback = False
get_weather.command = "!w"
get_weather.helptext = "Usage: \002!w <location>\002Example: !w hell, mi Shows weather info from a few different providers. Use \002!setlocation <location>\002 to save your location"

def get_hourly(self, e):
    try:
        location = e.location
    except:
        location = e.input
    if location and user.get_location(location):
        location = user.get_location(location) #allow looking up by nickname
    if location == "" and user:
        location = user.get_location(e.nick)
    onecall(self, e, location, True, False)
    return e

get_hourly.waitfor_callback = False
get_hourly.command = "!hourly"
#get_daily.helptext = "Usage: \002!w <location>\002Example: !w hell, mi Shows weather info from a few different providers. Use \002!setlocation <location>\002 to save your location"

def get_daily(self, e):
    try:
        location = e.location
    except:
        location = e.input
    if location and user.get_location(location):
        location = user.get_location(location) #allow looking up by nickname
    if location == "" and user:
        location = user.get_location(e.nick)
    
    onecall(self, e, location, False, True)
    return e

get_daily.waitfor_callback = False
get_daily.command = "!daily"
#get_daily.helptext = "Usage: \002!w <location>\002Example: !w hell, mi Shows weather info from a few different providers. Use \002!setlocation <location>\002 to save your location"

def get_forecast(self, e):
    try:
        location = e.location
    except:
        location = e.input
    if location and user.get_location(location):
        location = user.get_location(location) #allow looking up by nickname
    if location == "" and user:
        location = user.get_location(e.nick)
    onecall(self, e, location, False, True)        
    return e

get_forecast.waitfor_callback = False
get_forecast.command = "!forecast"
#get_daily.helptext = "Usage: \002!w <location>\002Example: !w hell, mi Shows weather info from a few different providers. Use \002!setlocation <location>\002 to save your location"

def onecall(self, e, location="", hourly=False, daily=False):
    apikey = self.botconfig["APIkeys"]["onecallAPIkey"]
    self.logger.debug("Entered onecall function. Location {} or {}".format(location, e.input))
    if location == "":
        location = e.input
    if location == "" and user:
        location = user.get_location(e.nick)
    try:
        address, lat, lng, country = self.tools['findLatLong'](location)
    except:
        e.output = "No location was found"
        return e
    exclude = ''
    #url = "https://dylix.org/test.json"
    url = "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&appid={}&units=imperial"
    url = url.format(lat, lng, apikey)
    #print(url)
    try:
        request = urllib.request.Request(url, None, {'Referer': 'https://dylix.org/'})
        response = urllib.request.urlopen(request)
        #print("skipping download")
        #with open("test.json", "r") as read_file:
        #    data = json.load(read_file)
        # UNCOMMENT RESULTS_JSON TOO
    except urllib.error.HTTPError as err:
        self.logger.exception("Exception in onecall:")
    
    #try:
    results_json = json.loads(response.read().decode('utf-8'))
    #results_json = data
    timezone_offset = results_json['timezone_offset']
    current_conditions = results_json['current']
    hourly_conditions = results_json['hourly']
    daily_conditions = results_json['daily']
    
    try:
        alerts = results_json['alerts']
    except KeyError:
        alerts = None
    if hourly:
        us_weather = f"{address}"
        world_weather = f"{address}"
        #for hour in hourly_conditions:
        for index, hour in enumerate(hourly_conditions):
            if index == 0 or (index % 2) == 0:
                reading_time = datetime.datetime.utcfromtimestamp(hour['dt']+results_json['timezone_offset'])
                wind_speed = int(round(hour['wind_speed'], 0))
                wind_speed_kmh = int(round(wind_speed * 1.609, 0))
                wind_direction = hour['wind_deg']
                wind_arrow = bearing_to_arrow(wind_direction)
                wind_direction = bearing_to_compass(wind_direction)
                reading_time_hour = reading_time.hour
                if reading_time_hour > 21:
                    break
                if reading_time_hour > 12:
                    reading_time_hour -= 12
                forecast_hour = "%s%s" % (reading_time_hour, reading_time.strftime("%p"))
                
                precip_chance = ''
                if hour['pop'] != 0:
                    precip_chance = f"Precip:{int(hour['pop'] * 100)}% "
                hour_precip_amount_combined = ''
                try:
                    snow_1h = hour['snow']['1h']
                    if country != "US":
                        hour_precip_amount_combined += f"Snow:{snow_1h}mm/h "
                    else:
                        hour_precip_amount_combined += f"Snow:{round((snow_1h/25.4),2)}in/h "
                except:
                    pass
                try:
                    rain_1h = hour['rain']['1h']
                    if country != "US":
                        hour_precip_amount_combined += f"Rain:{rain_1h}mm/h "
                    else:
                        hour_precip_amount_combined += f"Rain:{round((rain_1h/25.4),2)}in/h "
                except:
                    pass
                
                if country != "US":
                    world_weather += f" {forecast_hour} {fahrenheit_to_celsius(hour['temp'])}°C(Feels:{fahrenheit_to_celsius(hour['feels_like'])}°C) {precip_chance}{hour_precip_amount_combined}{wind_direction}{wind_arrow}@{wind_speed_kmh}kmh {hour['weather'][0]['description']} /"
                else:
                    us_weather += f" {forecast_hour} {int(hour['temp'])}°F(Feels:{int(hour['feels_like'])}°F) {precip_chance}{hour_precip_amount_combined}{wind_direction}{wind_arrow}@{wind_speed}mph {hour['weather'][0]['description']} /"

        if country != "US":
            world_weather = world_weather[0:-1]
            e.output = self.tools['insert_newline'](world_weather)
        else:
            us_weather = us_weather[0:-1]
            e.output = self.tools['insert_newline'](us_weather)
        return e
    elif daily:
        us_weather = f"{address}"
        world_weather = f"{address}"
        for day in daily_conditions:
            reading_time = datetime.datetime.utcfromtimestamp(day['dt']+results_json['timezone_offset'])
            wind_speed = int(round(day['wind_speed'], 0))
            wind_speed_kmh = int(round(wind_speed * 1.609, 0))
            wind_direction = day['wind_deg']
            wind_arrow = bearing_to_arrow(wind_direction)
            wind_direction = bearing_to_compass(wind_direction)
            summary_icon = weather_summary_to_icon(day['weather'][0]['icon'])
            forecast_day = reading_time.strftime("%A")

            precip_chance = ''
            if day['pop'] != 0:
                precip_chance = f"Precip:{int(day['pop'] * 100)}% "
            day_precip_amount_combined = ''
            try:
                snow_day = day['snow']
                if country != "US":
                    day_precip_amount_combined += f"Snow:{snow_day}mm "
                else:
                    day_precip_amount_combined += f"Snow:{round((snow_day/25.4),2)}in "
            except:
                pass
            try:
                rain_day = day['rain']
                if country != "US":
                    day_precip_amount_combined += f"Rain:{rain_day}mm "
                else:
                    day_precip_amount_combined += f"Rain:{round((rain_day/25.4),2)}in "
            except:
                pass

            if country != "US":
                world_weather += f" {forecast_day} L:{fahrenheit_to_celsius(day['temp']['min'])}°C/h:{fahrenheit_to_celsius(day['temp']['max'])}°C {precip_chance}{day_precip_amount_combined}{wind_direction}{wind_arrow}@{wind_speed_kmh}kmh {summary_icon}{day['weather'][0]['description']} /"
            else:
                us_weather += f" {forecast_day} L:{int(day['temp']['min'])}°F/H:{int(day['temp']['max'])}°F {precip_chance}{day_precip_amount_combined}{wind_direction}{wind_arrow}@{wind_speed}mph {summary_icon}{day['weather'][0]['description']} /"
        if country != "US":
            world_weather = world_weather[0:-1]
            e.output = self.tools['insert_newline'](world_weather)
        else:
            us_weather = us_weather[0:-1]
            e.output = self.tools['insert_newline'](us_weather)
        return e
    else:
        temp = current_conditions['temp']
        humidity = current_conditions['humidity']
        precip_probability = '' #current_conditions['precipProbability']
        current_summary = current_conditions['weather'][0]['description'].title()
        summary_icon = weather_summary_to_icon(current_conditions['weather'][0]['icon'])
        wind_speed = int(round(current_conditions['wind_speed'], 0))
        wind_speed_kmh = int(round(wind_speed * 1.609, 0))

        wind_direction = current_conditions['wind_deg']
        wind_arrow = bearing_to_arrow(wind_direction)
        wind_direction = bearing_to_compass(wind_direction)

        hour_precip_amount_combined = ''
        try:
            snow_1h = current_conditions['snow']['1h']
            if country != "US":
                hour_precip_amount_combined += f"Snow:{snow_1h}mm/h"
            else:
                hour_precip_amount_combined += f"Snow:{round((snow_1h/25.4),2)}in/h"
        except:
            pass
        try:
            rain_1h = current_conditions['rain']['1h']
            if country != "US":
                hour_precip_amount_combined += f"Rain:{rain_1h}mm/h"
            else:
                hour_precip_amount_combined += f"Rain:{round((rain_1h/25.4),2)}in/h"
        except:
            pass
        if hour_precip_amount_combined != '':
            hour_precip_amount_combined = f" {hour_precip_amount_combined} / "

        cloud_cover = current_conditions['clouds']
        feels_like = current_conditions['feels_like']
        min_temp = int(round(results_json['daily'][0]['temp']['min'],0))
        min_temp_c = int(round((min_temp - 32)*5/9,0)) 
        max_temp = int(round(results_json['daily'][0]['temp']['max'],0))
        max_temp_c = int(round((max_temp - 32)*5/9,0))
            
        if feels_like != temp:
            if country != "US":
                feels_like = " / Feels like: %s°C" % (int(round((feels_like- 32)*5/9,0)))
            else:
                feels_like = " / Feels like: %s°F" % (int(round(feels_like,0)))
        else:
            feels_like = ""
            
        temp_c = int(round((temp - 32)*5/9,0))
        temp = int(round(temp,0))

        timezone = pytz.timezone(results_json['timezone'])
        sunrise = datetime.datetime.utcfromtimestamp(current_conditions['sunrise']+results_json['timezone_offset'])
        sunset = datetime.datetime.utcfromtimestamp(current_conditions['sunset']+results_json['timezone_offset'])
        sunrise = timezone.localize(sunrise)
        sunset = timezone.localize(sunset)
        sunrise = sunrise.strftime('%-I:%M%p')
        sunset = sunset.strftime('%-I:%M%p')
        
        # If the minute by minute outlook isn't available, grab the hourly
        try:
            outlook = "%s -> %s " % (results_json['minutely'][0]['summary'].title(), results_json['daily'][0]['weather'][0]['description'].title())
        except:
            outlook = "%s -> %s" % (results_json['hourly'][12]['weather'][0]['description'].title(), results_json['daily'][0]['weather'][0]['description'].title())

        alert_urls = []
        if alerts:
            for alert in alerts:
                alert_sender_name = alert['sender_name']
                alert_event = alert['event']
                alert_start = datetime.datetime.fromtimestamp(alert['start'])
                alert_end = datetime.datetime.fromtimestamp(alert['end'])
                alert_description = alert['description']
                alert_tags = alert['tags']
                title = f"{alert_event} for {alert_sender_name}"
                content = f"{alert_event}\n\nStart time: {alert_start}\nEnd time: {alert_end}\n\n{alert_sender_name}\n{alert_description}\n\n{alert_tags}"
                alert_urls.append(hastebin(self, title, content))

        if country == "US": #If we're in the US, use Fahrenheit, otherwise Celsius    
            if (len(alert_urls) > 0):
                output = "{} / {} {} / {}°F{} / Humidity: {}% / Wind: {} {} at {} mph / Cloud Cover: {}% / High: {}°F Low: {}°F /{} Sunrise: {} Sunset: {} / Outlook: {}\n\nWeather Alert -> {}"
                e.output = output.format(address, current_summary, summary_icon, temp,
                                  feels_like, humidity, wind_arrow,
                                  wind_direction, wind_speed,
                                  cloud_cover, max_temp, min_temp, hour_precip_amount_combined, sunrise, sunset, outlook, *alert_urls)
            else:
                output = "{} / {} {} / {}°F{} / Humidity: {}% / Wind: {} {} at {} mph / Cloud Cover: {}% / High: {}°F Low: {}°F /{} Sunrise: {} Sunset: {} / Outlook: {}"
                e.output = output.format(address, current_summary, summary_icon, temp,
                                  feels_like, humidity, wind_arrow,
                                  wind_direction, wind_speed,
                                  cloud_cover, max_temp, min_temp, hour_precip_amount_combined, sunrise, sunset, outlook)
        else: #Outside of the US
            outlookt = re.search("(-?\d+)°F", outlook)
            if outlookt:
                try:
                    tmp = int(outlookt.group(1))
                    tmpstr = "{}°C".format(int(round((tmp - 32)*5/9,0)))
                    outlook = re.sub("-?\d+°F", tmpstr, outlook)
                except:
                    pass

            if (len(alert_urls) > 0):
                output = "{} / {} {} / {}°C{} / Humidity: {}% / Wind: {} {} at {} km/h / Cloud Cover: {}% / High: {}°C Low: {}°C /{} Sunrise: {} Sunset: {} / Outlook: {}\n\nWeather Alert -> {}"
                e.output = output.format(address, current_summary, summary_icon, temp_c,
                                  feels_like, humidity, wind_arrow, wind_direction,
                                  wind_speed_kmh, cloud_cover, max_temp_c,
                                  min_temp_c, hour_precip_amount_combined, sunrise, sunset, outlook, *alert_urls)
            else:
                output = "{} / {} {} / {}°C{} / Humidity: {}% / Wind: {} {} at {} km/h / Cloud Cover: {}% / High: {}°C Low: {}°C /{} Sunrise: {} Sunset: {} / Outlook: {}"
                e.output = output.format(address, current_summary, summary_icon, temp_c,
                                  feels_like, humidity, wind_arrow, wind_direction,
                                  wind_speed_kmh, cloud_cover, max_temp_c,
                                  min_temp_c, hour_precip_amount_combined, sunrise, sunset, outlook)
        return e

def pasteglotio(self, title, content):
    headers = {"Content-type": "text/plain" }
    #data = { "title": title, "content": content }
    data = f'{{"language": "python", "title": "{title}", "public": "false", "files": [{{"name": "weather-alert.txt", "content": "{content}"}}]}}'

    data = multiline.loads(data, multiline=True)
    print(headers)
    print(data)
    response = requests.post("https://glot.io/api/snippets", data=data, headers=headers)
    paste = response.json()
    print(paste)
    return paste['url']

def hastebin(self, title, content):
    api_key = self.botconfig["APIkeys"]["hastebinAPIkey"]
    headers = {"Authorization": "Bearer " + api_key, "content-type": "text/plain" }
    data = content
    response = requests.post("https://hastebin.com/documents", data=data, headers=headers)
    paste = response.json()
    return "https://hastebin.com/share/" + paste['key']

def pastebin(self, title, content):
    #inner function cus why not
    def paste(username, password, api_key, privacity, title, content):
        if not username or not password or not api_key:
            raise ValueError("username, password, api key, privacity code, title and content has to be specified.")
        else:
            data = {
                "api_option": "paste",
                "api_dev_key": api_key,
                "api_paste_code": content,
                "api_paste_name": title,
                "api_paste_expire_date": "1H",
                "api_user_key": None,
                "api_paste_format": "php",
                "api_paste_private": privacity,
                }
            paste = requests.post("https://pastebin.com/api/api_post.php", data=data)
            if "https://pastebin.com" in paste.text:
                return (paste.text).replace("https://pastebin.com/", "https://pastebin.com/raw/")
            else:
               return paste.text
    # Upload a paste on an account
    api_key = self.botconfig["APIkeys"]["pastebinAPIkey"]
    privacy = "1" # 0 : public | 1 : unlisted | 2 : private
    username = 'a'
    password = 'b'
    return paste(username, password, api_key, privacy, title, content)
    #print(pastebinapi.url(setting="1")) # get pastebin url
    
def get_sun(self, e):
    try:
        location = e.location
    except:
        location = e.input
    
    if location and user.get_location(location):
        location = user.get_location(location) #allow looking up by nickname
    
    if location == "" and user:
        location = user.get_location(e.nick)
    apikey = self.botconfig["APIkeys"]["onecallAPIkey"]
    self.logger.debug("Entered sun function. Location {} or {}".format(location, e.input))
    if location == "":
        location = e.input
    if location == "" and user:
        location = user.get_location(e.nick)
    try:
        address, lat, lng, country = self.tools['findLatLong'](location)
    except:
        e.output = "No location was found"
        return e
    exclude = ''
    url = "https://api.openweathermap.org/data/2.5/onecall?lat={}&lon={}&appid={}&units=imperial"
    url = url.format(lat, lng, apikey)
    #print(url)
    try:
        request = urllib.request.Request(url, None, {'Referer': 'https://dylix.org/'})
        response = urllib.request.urlopen(request)
        #print("skipping download")
        #with open("test.json", "r") as read_file:
        #    data = json.load(read_file)
        # UNCOMMENT RESULTS_JSON TOO
    except urllib.error.HTTPError as err:
        self.logger.exception("Exception in onecall:")
    
    #try:
    results_json = json.loads(response.read().decode('utf-8'))
    #results_json = data
    timezone_offset = results_json['timezone_offset']
    
    daily_conditions = results_json['daily'][0]

    timezone = pytz.timezone(results_json['timezone'])
    time = datetime.datetime.utcfromtimestamp(daily_conditions['dt']+results_json['timezone_offset'])
    sunrise = datetime.datetime.utcfromtimestamp(daily_conditions['sunrise']+results_json['timezone_offset'])
    sunset = datetime.datetime.utcfromtimestamp(daily_conditions['sunset']+results_json['timezone_offset'])
    time = timezone.localize(time)
    sunrise = timezone.localize(sunrise)
    sunset = timezone.localize(sunset)

    #time = time.strftime('%H:%M%p')
    #sunrise = sunrise.strftime('%H:%M%p')
    #sunset = sunset.strftime('%H:%M%p')

    sunriseobj = sunrise
    sunsetobj = sunset
    #now = datetime.datetime.strptime(time, "%H:%M%p")
    #sunriseobj = datetime.datetime.strptime(sunrise, "%H:%M%p")
    #sunsetobj = datetime.datetime.strptime(sunset, "%H:%M%p")
    now = timezone.localize(datetime.datetime.utcnow()+datetime.timedelta(seconds=results_json['timezone_offset']))
    #now = datetime.datetime.utcnow()
    #now = time

    sunlength = sunsetobj - sunriseobj
    if sunriseobj > now:
       ago = "from now"
       td = sunriseobj - now
    else:
       td = now - sunriseobj
       ago = "ago"
    til = self.tools['prettytimedelta'](td)
    sunrise = "{} ({} {})".format(sunrise.strftime('%-I:%M%p'), til, ago)
    if sunsetobj > now:
       ago = "from now"
       td = sunsetobj - now
    else:
       ago = "ago"
       td = now - sunsetobj
    til = self.tools['prettytimedelta'](td)
    sunset = "{} ({} {})".format(sunset.strftime('%-I:%M%p'), til, ago)

    out = "Sunrise: {} / Sunset: {} / Day Length: {}".format(sunrise, sunset, sunlength)
    e.output = out
    return e
get_sun.command = "!sun"
get_sun.helptext = "Usage: \002!sun <location>\002Example: !sun 59711 Show information about sunrise and sunset Use \002!setlocation <location>\002 to save your location"