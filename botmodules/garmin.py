import json, urllib.request, urllib.error, urllib.parse, re, botmodules.purpleair as purpleair
import datetime
import json
import logging
import os
import sys
import math
from getpass import getpass

import readchar
import requests
from garth.exc import GarthHTTPError

from garminconnect import (
    Garmin,
    GarminConnectAuthenticationError,
    GarminConnectConnectionError,
    GarminConnectTooManyRequestsError,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

email = os.getenv("EMAIL")
password = os.getenv("PASSWORD")
tokenstore = os.getenv("GARMINTOKENS") or "~/.garminconnect"
tokenstore_base64 = os.getenv("GARMINTOKENS_BASE64") or "~/.garminconnect_base64"
api = None

def dylix(self, e):
    try:
        if (e.input == "avg"):
            today = datetime.date.today()
            startdate = today - datetime.timedelta(days=30)  # Select past week
            api = init_api(email, password)
            response = api.get_weigh_ins(startdate, today.isoformat())
            e.output = f"dylix's garmin scale 30 day average | Weight: {round(int(response['totalAverage']['weight'])/1000*2.205,2)}lbs | BMI: {round(float(response['totalAverage']['bmi']),2)} | Body Fat: {response['totalAverage']['bodyFat']}% | Body Water: {response['totalAverage']['bodyWater']}% | Bone Mass: {round(int(response['totalAverage']['boneMass'])/1000*2.205,2)}lbs | Muscle Mass: {round(int(response['totalAverage']['muscleMass'])/1000*2.205,2)}lbs"
        else:
            today = datetime.date.today()
            api = init_api(email, password)
            response = api.get_daily_weigh_ins(today.isoformat())
            #response = {"startDate": "2024-03-25", "endDate": "2024-03-25", "dateWeightList": [{"samplePk": 1711385150750, "date": 1711363527000, "calendarDate": "2024-03-25", "weight": 74900.0, "bmi": 23.100000381469727, "bodyFat": 16.2, "bodyWater": 61.2, "boneMass": 4710, "muscleMass": 31600, "physiqueRating": None, "visceralFat": None, "metabolicAge": None, "sourceType": "INDEX_SCALE", "timestampGMT": 1711385127000, "weightDelta": 45.35923699999742}], "totalAverage": {"from": 1711324800000, "until": 1711411199999, "weight": 74900.0, "bmi": 23.100000381469727, "bodyFat": 16.2, "bodyWater": 61.2, "boneMass": 4710, "muscleMass": 31600, "physiqueRating": None, "visceralFat": None, "metabolicAge": None}}
            e.output = f"dylix's Garmin Scale @ {response['startDate']} Weight: {round(int(response['dateWeightList'][0]['weight'])/1000*2.205,2)}lbs | BMI: {round(float(response['dateWeightList'][0]['bmi']),2)} | Body Fat: {response['dateWeightList'][0]['bodyFat']}% | Body Water: {response['dateWeightList'][0]['bodyWater']}% | Bone Mass: {round(int(response['dateWeightList'][0]['boneMass'])/1000*2.205,2)}lbs | Muscle Mass: {round(int(response['dateWeightList'][0]['muscleMass'])/1000*2.205,2)}lbs"
    except Exception as err:
        today = datetime.date.today()
        startdate = today - datetime.timedelta(days=30)  # Select past week
        api = init_api(email, password)
        response = api.get_weigh_ins(startdate, today.isoformat())
        e.output = f"dylix's garmin scale 30 day average | Weight: {round(int(response['totalAverage']['weight'])/1000*2.205,2)}lbs | BMI: {round(float(response['totalAverage']['bmi']),2)} | Body Fat: {response['totalAverage']['bodyFat']}% | Body Water: {response['totalAverage']['bodyWater']}% | Bone Mass: {round(int(response['totalAverage']['boneMass'])/1000*2.205,2)}lbs | Muscle Mass: {round(int(response['totalAverage']['muscleMass'])/1000*2.205,2)}lbs"
    return e

dylix.command = "!scale"
dylix.helptext = "!scale - gets dylix's scale info"

def get_credentials():
    """Get user credentials."""

    email = input("Login e-mail: ")
    password = getpass("Enter password: ")

    return email, password


def init_api(email, password):
    """Initialize Garmin API with your credentials."""

    try:
        # Using Oauth1 and OAuth2 token files from directory
        #print(
        #    f"Trying to login to Garmin Connect using token data from directory '{tokenstore}'...\n"
        #)

        # Using Oauth1 and Oauth2 tokens from base64 encoded string
        # print(
        #     f"Trying to login to Garmin Connect using token data from file '{tokenstore_base64}'...\n"
        # )
        # dir_path = os.path.expanduser(tokenstore_base64)
        # with open(dir_path, "r") as token_file:
        #     tokenstore = token_file.read()

        garmin = Garmin()
        garmin.login(tokenstore)

    except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError):
        # Session is expired. You'll need to log in again
        print(
            "Login tokens not present, login with your Garmin Connect credentials to generate them.\n"
            f"They will be stored in '{tokenstore}' for future use.\n"
        )
        try:
            # Ask for credentials if not set as environment variables
            if not email or not password:
                email, password = get_credentials()

            garmin = Garmin(email, password)
            garmin.login()
            # Save Oauth1 and Oauth2 token files to directory for next login
            garmin.garth.dump(tokenstore)
            print(
                f"Oauth tokens stored in '{tokenstore}' directory for future use. (first method)\n"
            )
            # Encode Oauth1 and Oauth2 tokens to base64 string and safe to file for next login (alternative way)
            token_base64 = garmin.garth.dumps()
            dir_path = os.path.expanduser(tokenstore_base64)
            with open(dir_path, "w") as token_file:
                token_file.write(token_base64)
            print(
                f"Oauth tokens encoded as base64 string and saved to '{dir_path}' file for future use. (second method)\n"
            )
        except (FileNotFoundError, GarthHTTPError, GarminConnectAuthenticationError, requests.exceptions.HTTPError) as err:
            logger.error(err)
            return None

    return garmin

def request_json(url):
    #headers = {'Authorization': 'access_token ' + request_json.token}
    # print ("Strava: requesting %s Headers: %s" % (url, headers))
    headers = {}
    req = urllib.request.Request(url, None, headers)
    response = urllib.request.urlopen(req)
    response = json.loads(response.read().decode('utf-8'))
    return response