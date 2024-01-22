import json, urllib.request, urllib.error, urllib.parse, re, botmodules.purpleair as purpleair
import requests

def checkIfUserIsStreaming(username):
    try:
        url = "https://gql.twitch.tv/gql"
        query = "query {\n  user(login: \""+username+"\") {\n    stream {\n      id\n    }\n  }\n}"
        #the client-id is taken from Twitch's website. Twitch uses the client-id to fetch information for anonymous users. It will always work, without the need of getting your own client-id.
        return True if requests.request("POST", url, json={"query": query, "variables": {}}, headers={"client-id": "kimne78kx3ncx6brgo4mv6wki5h1ko"}).json()["data"]["user"]["stream"] else False
    except:
        return False

def twitch_live(self, e):
    if e.input == '':
        username = 'dylix'
    else:
        username = e.input
    if checkIfUserIsStreaming(username):
        e.output = f"Yay, {username} is streaming. https://twitch.tv/{username}"
    else:
        e.output = f"Aww, {username} isn't streaming. https://twitch.tv/{username}"
    return e

twitch_live.command = "!twitch"
twitch_live.helptext = "!twitch - returns if a stream is live or not"

def request_json(url):
    #headers = {'Authorization': 'access_token ' + request_json.token}
    # print ("Strava: requesting %s Headers: %s" % (url, headers))
    headers = {}
    req = urllib.request.Request(url, None, headers)
    response = urllib.request.urlopen(req)
    response = json.loads(response.read().decode('utf-8'))
    return response