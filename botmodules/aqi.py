import mock
import unittest
import requests
import datetime
from copy import deepcopy
import openmeteo_requests
from openmeteo_sdk.Variable import Variable
import math
import sys

error_msg = "Could not retrieve current air quality data."
json_error_msg = "JSON schema in response has changed. Please fix me. Key error: {}"
location_missing_msg = "Use !setlocation <location> to save your location to the bot or use !aqi <zipcode>"
# http://en.wikipedia.org/wiki/Extreme_points_of_the_United_States#Westernmost
top = 49.3457868 # north lat
left = -124.7844079 # west long
right = -66.9513812 # east long
bottom =  24.7433195 # south lat

def IsUSA(latlngs):
    """ Accepts a list of lat/lng tuples. 
        returns the list of tuples that are within the bounding box for the US.
        NB. THESE ARE NOT NECESSARILY WITHIN THE US BORDERS!
    """
    inside_box = []
    for (lat, lng) in latlngs:
        if bottom <= lat <= top and left <= lng <= right:
            #inside_box.append((lat, lng))
            return True
    #return inside_box
    return False

def get_zipcode(self, lat, lng):
    url = f"http://api.geonames.org/findNearbyPostalCodesJSON?lat={lat}&lng={lng}&username=dylix"
    try:
        current_response = requests.get(url).json()
        return current_response['postalCodes'][0]['postalCode']
    except:
        return None

def get_euroaqi(self, botevent, address, lat, lng, country):
    #print(f"euro aqi: {self} {address} {lat} {lng} {country}")
    openmeteo = openmeteo_requests.Client()

    # Make sure all required weather variables are listed here
    # The order of variables in hourly or daily is important to assign them correctly below
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"
    params = {
        "latitude": lat,
        "longitude": lng,
        "current": ["pm10", "pm2_5", "european_aqi"]
    }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]    
    # Current values
    current = response.Current()
    current_european_aqi = current.Variables(2).Value()
    current_variables = list(map(lambda i: current.Variables(i), range(0, current.VariablesLength())))
    #current_temperature_2m = next(filter(lambda x: x.Variable() == Variable.temperature and x.Altitude() == 2, current_variables))
    #current_relative_humidity_2m = next(filter(lambda x: x.Variable() == Variable.relative_humidity and x.Altitude() == 2, current_variables))

    #print(f"Current time {current.Time()}")
    pm10 = current_variables[0].Value()
    pm2p5 = current_variables[1].Value()
    #print(f"Current temperature_2m {current_temperature_2m.Value()}")
    #print(f"Current relative_humidity_2m {current_relative_humidity_2m.Value()}")
    botevent.output = f"Air quality: {address} | EAQI: {math.floor(current_european_aqi)} | PM2.5: {calcAQIpm25(pm2p5)} | PM10: {calcAQIpm10(pm10)}"
    #botevent.output = f"{location} - Air quality: {current_pm}{current_ozone}{tomorrow_forecast}"
    return botevent


def get_aqi(self, botevent):
    zipcode = ""
    address = ""
    lat = ""
    lng = ""
    country = ""
    try:
        zipcode = botevent.input if botevent.input else botevent.user_location
        if zipcode.isdigit() is False:
            if not zipcode:
                if not botevent.input:
                    zipcode = sys.modules['botmodules.userlocation'].get_location(botevent.user_location)
                    if zipcode:
                        address, lat, lng, country = self.tools['findLatLong'](zipcode)
                else:
                    address, lat, lng, country = self.tools['findLatLong'](botevent.input)
                    if not address:
                        zipcode = sys.modules['botmodules.userlocation'].get_location(botevent.input)
                        address, lat, lng, country = self.tools['findLatLong'](zipcode)
            else:
                if not botevent.input:
                    if not zipcode:
                        zipcode = sys.modules['botmodules.userlocation'].get_location(botevent.user_location)
                else:
                    zipcode = sys.modules['botmodules.userlocation'].get_location(zipcode)
                    if not zipcode:
                        #zipcode = sys.modules['botmodules.userlocation'].get_location(botevent.input)
                        zipcode = botevent.input
                try:
                    address, lat, lng, country = self.tools['findLatLong'](zipcode)
                except:
                    botevent.output = "Could not find matching location. Using State or Country? Use only two letter abbreviations"
                    return botevent
            if IsUSA([(lat,lng)]):
                zipcode = get_zipcode(self, lat, lng)
            else:
                return get_euroaqi(self, botevent, address, lat, lng, country)
        else:
            address, lat, lng, country = self.tools['findLatLong'](zipcode)
            zipcode = get_zipcode(self, lat, lng)
    except AttributeError:
        pass
    if not zipcode:
        botevent.output = location_missing_msg
        return botevent

    try:
        api_key = self.botconfig["APIkeys"]["airnow_apikey"]
    except KeyError as error:
        self.logger.error(f"airnow.gov API key not set. Key not found: {error}")
        return botevent

    date_format = "%Y-%m-%d"
    today = datetime.datetime.today().strftime(date_format)
    tomorrow = (datetime.datetime.today() + datetime.timedelta(days=+1)).strftime(date_format)


    forecast_url = f"http://www.airnowapi.org/aq/forecast/zipCode/?format=application/json&zipCode={zipcode}&date={today}&distance=25&API_KEY={api_key}"
    current_url = f"http://www.airnowapi.org/aq/observation/zipCode/current/?format=application/json&zipCode={zipcode}&distance=25&API_KEY={api_key}"

    current_response = []
    forecast_response = []

    try:
        current_response = requests.get(current_url).json()
        forecast_response = requests.get(forecast_url).json()
    except Exception:
        self.logger.exception(error_msg)
        botevent.output = error_msg

    if not current_response:
        botevent.output = error_msg
        return botevent

    current_ozone = ""
    current_pm = ""
    location = ""
    tomorrow_forecast = ""

    try:
        for observation in current_response:
            if observation['ParameterName'] == "O3":
                current_ozone = f"AQI: {observation['AQI']} ({observation['Category']['Name']})"
                location = f"{observation['ReportingArea']}, {observation['StateCode']}"
            elif 'PM' in observation['ParameterName']:
                current_pm = f"{current_pm}{observation['ParameterName']}: {observation['AQI']} ({observation['Category']['Name']}) "
                location = f"{observation['ReportingArea']}, {observation['StateCode']}"
    except KeyError as error:
        botevent.output = f"{json_error_msg.format(error)}"
        return botevent

    try:
        for forecast in forecast_response:
            if forecast['DateForecast'].strip() == tomorrow and forecast['AQI'] != -1:
                tomorrow_forecast = f" Tomorrow: {forecast['ParameterName']}: {forecast['AQI']} ({forecast['Category']['Name']})"
    except KeyError:
        pass

    botevent.output = f"{location} - Air quality: {current_pm}{current_ozone}{tomorrow_forecast}"
    return botevent

get_aqi.command = "!aqi"
get_aqi.helptext = "Usage: !aqi <zipcode> Retrieves air quality info from airnow.gov"

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

class TestEvent(object):
    def __init__(self):
        self.input = "90210"
        self.output = ""
        self.user_location = ""

class TestBot(object):
    def __init__(self):
        self.logger = mock.MagicMock()
        self.logger.exception = mock.MagicMock()
        self.botconfig = {"APIkeys": {"airnow_apikey": None}}

class AQITests(unittest.TestCase):
    date_format = "%Y-%m-%d"
    today = datetime.datetime.today().strftime(date_format)
    tomorrow = (datetime.datetime.today() + datetime.timedelta(days=+1)).strftime(date_format)

    current_response = [{'AQI': 4,
                         'Category': {'Name': 'Good', 'Number': 1},
                         'DateObserved': '{} '.format(today),
                         'HourObserved': 7,
                         'Latitude': 37.33,
                         'LocalTimeZone': 'PST',
                         'Longitude': -121.9,
                         'ParameterName': 'O3',
                         'ReportingArea': 'San Jose',
                         'StateCode': 'CA'},
                        {'AQI': 70,
                         'Category': {'Name': 'Moderate', 'Number': 2},
                         'DateObserved': '{} '.format(today),
                         'HourObserved': 7,
                         'Latitude': 37.33,
                         'LocalTimeZone': 'PST',
                         'Longitude': -121.9,
                         'ParameterName': 'PM2.5',
                         'ReportingArea': 'San Jose',
                         'StateCode': 'CA'}]

    forecast_response = [{'AQI': 161,
                          'ActionDay': False,
                          'Category': {'Name': 'Unhealthy', 'Number': 4},
                          'DateForecast': '{} '.format(today),
                          'DateIssue': '2017-10-11 ',
                          'Latitude': 37.33,
                          'Longitude': -121.9,
                          'ParameterName': 'PM2.5',
                          'ReportingArea': 'San Jose',
                          'StateCode': 'CA'},
                         {'AQI': 181,
                          'ActionDay': False,
                          'Category': {'Name': 'Unhealthy for Sensitive Groups', 'Number': 3},
                          'DateForecast': '{} '.format(tomorrow),
                          'DateIssue': '2017-10-11 ',
                          'Latitude': 37.33,
                          'Longitude': -121.9,
                          'ParameterName': 'PM2.5',
                          'ReportingArea': 'San Jose',
                          'StateCode': 'CA'},
                         {'AQI': -1,
                          'ActionDay': False,
                          'Category': {'Name': 'Unhealthy for Sensitive Groups', 'Number': 3},
                          'DateForecast': '2017-10-14 ',
                          'DateIssue': '2017-10-11 ',
                          'Latitude': 37.33,
                          'Longitude': -121.9,
                          'ParameterName': 'PM2.5',
                          'ReportingArea': 'San Jose',
                          'StateCode': 'CA'},
                         {'AQI': -1,
                          'ActionDay': False,
                          'Category': {'Name': 'Unhealthy for Sensitive Groups', 'Number': 3},
                          'DateForecast': '2017-10-15 ',
                          'DateIssue': '2017-10-11 ',
                          'Latitude': 37.33,
                          'Longitude': -121.9,
                          'ParameterName': 'PM2.5',
                          'ReportingArea': 'San Jose',
                          'StateCode': 'CA'},
                         {'AQI': -1,
                          'ActionDay': False,
                          'Category': {'Name': 'Moderate', 'Number': 2},
                          'DateForecast': '2017-10-16 ',
                          'DateIssue': '2017-10-11 ',
                          'Latitude': 37.33,
                          'Longitude': -121.9,
                          'ParameterName': 'PM2.5',
                          'ReportingArea': 'San Jose',
                          'StateCode': 'CA'}]

    desired_output_with_forecast = "San Jose, CA - Air quality: PM2.5: 70 (Moderate) Ozone: 4 (Good) Tomorrow: PM2.5: 181 (Unhealthy for Sensitive Groups)"
    desired_output_without_forecast = "San Jose, CA - Air quality: PM2.5: 70 (Moderate) Ozone: 4 (Good)"

    def setUp(self):
        self.test_bot = TestBot()
        self.test_event = TestEvent()

    @mock.patch("requests.get", autospec=True)
    def test_aqi_with_input(self, mock_get):
        self.test_event.input = "95125"
        self.test_event.user_location = ""

        mock_response = mock.MagicMock()
        mock_response.json.side_effect = [self.current_response, self.forecast_response]
        mock_get.return_value = mock_response
        

        result = get_aqi(self.test_bot, self.test_event)

        self.assertEqual(mock_response.json.call_count, 2)
        self.assertEqual(result.output, self.desired_output_with_forecast)

    def test_aqi_missing_api_key(self):
        # Missing API key
        self.test_bot.botconfig['APIkeys'].pop("airnow_apikey")
        result = get_aqi(self.test_bot, self.test_event)
        self.assertEqual(result.output, "")

    @mock.patch("requests.get")
    def test_aqi_no_input_no_saved_location(self, mock_get):
        self.test_event.input = ""
        self.test_event.user_location = ""

        result = get_aqi(self.test_bot, self.test_event)
        self.assertIsNotNone(result)
        self.assertEqual(result.output, location_missing_msg)
        mock_get.assert_not_called()

    @mock.patch("requests.get")
    def test_aqi_no_input_yes_saved_location(self, mock_get):
        self.test_event.input = ""
        self.test_event.user_location = "95125"

        mock_response = mock.MagicMock()
        mock_response.json.side_effect = [self.current_response, self.forecast_response]
        mock_get.return_value = mock_response

        result = get_aqi(self.test_bot, self.test_event)
        self.assertIsNotNone(result)
        self.assertEqual(mock_response.json.call_count, 2)
        self.assertEqual(result.output, self.desired_output_with_forecast)

    @mock.patch("requests.get")
    def test_aqi_yes_input_yes_saved_location(self, mock_get):
        self.test_event.input = "90210"
        self.test_event.user_location = "95125"

        mock_response = mock.MagicMock()
        mock_response.json.side_effect = [self.current_response, self.forecast_response]
        mock_get.return_value = mock_response

        result = get_aqi(self.test_bot, self.test_event)
        self.assertIsNotNone(result)
        self.assertEqual(mock_response.json.call_count, 2)
        self.assertEqual(result.output, self.desired_output_with_forecast)

        #Check that we're using the input and not saved user location
        for call in mock_get.call_args_list:
            self.assertIn(self.test_event.input, call[0][0])



    @mock.patch("requests.get", autospec=True)
    def test_aqi_negative(self, mock_get):

        # Exception when trying to fetch URL
        desired_output = error_msg
        mock_response = mock.MagicMock()
        mock_response.json.side_effect = Exception
        mock_get.return_value = mock_response
        result = get_aqi(self.test_bot, self.test_event)
        self.assertEqual(result.output, desired_output)
        self.test_bot.logger.exception.assert_called_with(error_msg)

        # Test with empty response
        mock_response.json.side_effect = None
        mock_response.json.return_value = []

        result = get_aqi(self.test_bot, self.test_event)
        self.assertEqual(result.output, desired_output)

        # Missing stuff from the current response
        desired_output = json_error_msg.format("'AQI'")
        mock_response.json.side_effect = None
        broken_response = deepcopy(self.current_response)
        broken_response[0].pop('AQI')

        mock_response.json.return_value = broken_response

        result = get_aqi(self.test_bot, self.test_event)
        self.assertEqual(result.output, desired_output)

        # Missing stuff from the Forecast response
        broken_response = deepcopy(self.forecast_response)
        for response in broken_response:
            response.pop('AQI')
        mock_response.json.side_effect = [self.current_response, broken_response]
        result = get_aqi(self.test_bot, self.test_event)
        self.assertEqual(result.output, self.desired_output_without_forecast)

    @unittest.skip("Enable this yourself to test against the real API")
    def test_aqi_real(self):
        api_key = "CHANGE ME"
        self.test_bot.botconfig = {"APIkeys":
                                        {"airnow_apikey": api_key}}


        result = get_aqi(self.test_bot, self.test_event)
        print(result.output)


if __name__ == "__main__":
    unittest.main()
