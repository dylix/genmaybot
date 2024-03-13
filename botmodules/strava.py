import re
import sqlite3
import urllib.request
import json
import datetime
import time
import cherrypy, threading
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import random
import math

# End Web server stuff
def check_strava_token(self, user, token, refresh, returnAthlete = False):
    #print('checking token')
    url = "https://www.strava.com/api/v3/athlete"
    try:
        headers = {'Authorization': 'Bearer ' + token}
        req = urllib.request.Request(url, None, headers)
        response = urllib.request.urlopen(req)
        response = json.loads(response.read().decode('utf-8'))
        return True
    except Exception as e:
        if refresh_strava_token(self, user, token, refresh):
            return "refreshed"
        return False

def refresh_strava_token(self, user, token, refresh):
    #print('refreshing token')
    strava_client_secret = self.botconfig["APIkeys"]["stravaClientSecret"]
    strava_client_id = self.botconfig["APIkeys"]["stravaClientId"]
    params = urllib.parse.urlencode({'client_id': strava_client_id, 'client_secret': strava_client_secret, 'refresh_token': refresh, 'grant_type': 'refresh_token'})
    params = params.encode('utf-8')
    req = urllib.request.Request("https://www.strava.com/oauth/token")
    req.add_header("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")
    try:
        response = urllib.request.urlopen(req, params)
        response = json.loads(response.read().decode('utf-8'))
        strava_insert_token(user, response['access_token'], response['refresh_token'])
        request_json.token = response['access_token']
        request_json.refresh = response['refresh_token']
        return True
    except Exception as err:
        return False

def strava_get_token(user):
    #print('get token localdb')
    """ Get an token by user """
    conn = sqlite3.connect('strava.sqlite')
    c = conn.cursor()
    query = "SELECT token,refresh FROM tokens WHERE lower(user) = :user"

    try:
        result = c.execute(query, {'user': user.lower()}).fetchone()
    except Exception as err:
        return None, None #False
    if result:
        c.close()
        return result[0], result[1]
    else:
        c.close()
        return None, None #False

def strava_oath_code(self, e, state=None, code=None, error=None):
    strava_client_secret = self.botconfig["APIkeys"]["stravaClientSecret"]
    strava_client_id = self.botconfig["APIkeys"]["stravaClientId"]
    state = e.nick
    code = e.input.split(' ')[2]
    if code and state:
        params = urllib.parse.urlencode({'client_id': strava_client_id, 'client_secret': strava_client_secret, 'code': code, 'grant_type': 'authorization_code'})
        params = params.encode('utf-8')
        req = urllib.request.Request("https://www.strava.com/oauth/token")
        req.add_header("Content-Type", "application/x-www-form-urlencoded;charset=utf-8")
        # pdb.set_trace()
        try:
            response = urllib.request.urlopen(req, params)
            response = json.loads(response.read().decode('utf-8'))
            strava_insert_athlete(e.nick, response['athlete']['id'])
            strava_insert_token(e.nick, response['access_token'], response['refresh_token'])
            e.output = "Strava token exchange completed successfully. You can close this window now."
            return e
        except Exception as err:
            e.output = f"{err} Token exchange with Strava failed. Please try to authenticate again."
            return e


    elif (error != None) or (code == None):
        return "Invalid or empty access code received from Strava. Please try to authenticate again."

def strava_insert_token(user, token, refresh):
    """ Insert a user's strava token into the token table """
    conn = sqlite3.connect('strava.sqlite')
    c = conn.cursor()
    query = "INSERT INTO tokens VALUES (:user, :token, :refresh)"
    c.execute(query, {'user': user.lower(), 'token': token, 'refresh': refresh})
    #c.execute(f"INSERT INTO tokens VALUES (?, ?);", user, token)
    conn.commit()
    c.close()

def strava_oauth_exchange(self, e):
    strava_client_secret = self.botconfig["APIkeys"]["stravaClientSecret"]
    strava_client_id = self.botconfig["APIkeys"]["stravaClientId"]
    nick = e.nick
    # Send the user off to Strava to authorize us
    strava_redirect_url = "https://dylix.org/strava/callback?stravaId=%s" % (nick)
    strava_oauth_url = "https://www.strava.com/oauth/authorize?client_id=%s&response_type=code&redirect_uri=%s&scope=&scope=read,activity:read,activity:read_all,profile:read_all,&approval_prompt=force" % (strava_client_id, strava_redirect_url)
    self.irccontext.privmsg(e.nick, "Load this URL in your web browser and authorize the bot:")
    self.irccontext.privmsg(e.nick, strava_oauth_url)
    e.output = "Check your PM for further info to complete the auth process."
    return e

# this is only needed if we ever have to change the strava token
def set_stravatoken(line, nick, self, c):
    self.botconfig["APIkeys"]["stravaToken"] = line[12:]
    with open('genmaybot.cfg', 'w') as configfile:
        self.botconfig.write(configfile)
set_stravatoken.admincommand = "stravatoken"

def set_stravaclientid(line, nick, self, c):
    self.botconfig["APIkeys"]["stravaClientId"] = line[15:]
    with open('genmaybot.cfg', 'w') as configfile:
        self.botconfig.write(configfile)
set_stravaclientid.admincommand = "stravaclientid"

def set_stravaclientsecret(line, nick, self, c):
    self.botconfig["APIkeys"]["stravaClientSecret"] = line[19:]
    with open('genmaybot.cfg', 'w') as configfile:
        self.botconfig.write(configfile)
set_stravaclientsecret.admincommand = "stravaclientsecret"

def __init__(self):
    """ On init, read the token to a variable, then do a system check which runs upgrades and creates tables. """
    strava_check_system()  # Check the system for tables and/or upgrades

    strava_client_secret = self.botconfig["APIkeys"]["stravaClientSecret"]
    strava_client_id = self.botconfig["APIkeys"]["stravaClientId"]

def request_json(url):
    #print('requesting json: ', url)
    #if not request_json.token:  # if we haven't found a valid client token, fall back to the public one
    #    request_json.token = self.botconfig["APIkeys"]["stravaToken"]
    headers = {'Authorization': 'access_token ' + request_json.token}
    #print ("Strava: requesting %s Headers: %s" % (url, headers))
    response = ''
    req = ''
    try:
        req = urllib.request.Request(url, None, headers)
        response = urllib.request.urlopen(req)
        response = json.loads(response.read().decode('utf-8'))
    except Exception as err:
        print(f'rjson ex:{err}')
    return response

def strava_software_version():
    """ Returns the current version of the strava module, used upgrade """
    return 1

def strava_check_system():
    """ Run upgrades and check on initial table creation/installation """
    strava_check_upgrades()
    strava_check_create_tables()

def strava_check_upgrades():
    """ Check the version in the database and upgrade the system recursively until we're at the current version """
    software_version = strava_get_version('software')
    latest_version = strava_software_version()
    if software_version == False:
        # This must be a new revision
        # we need to set it to the current version that is being installed.
        strava_set_version('software', latest_version)
        strava_check_upgrades()
    elif software_version < strava_software_version():
        # Then we need to perform an upgrade for this version.
        func = 'strava_upgrade_%s' % (software_version + 1)
        globals()[func]()
        strava_check_upgrades()

def strava_set_version(version_field, version_number):
    """ Sets a version number for any component """
    conn = sqlite3.connect('strava.sqlite')
    c = conn.cursor()
    query = "INSERT INTO version VALUES (:version_field, :version_number)"
    c.execute(query,
              {'version_field': version_field,
               'version_number': version_number})
    conn.commit()
    c.close()

def strava_get_version(version_field):
    """ Get the version for a component of code """
    strava_check_create_tables()
    conn = sqlite3.connect('strava.sqlite')
    c = conn.cursor()
    query = "SELECT version_number FROM version WHERE version_field = :version_field"
    result = c.execute(query, {'version_field': version_field}).fetchone()
    if result:
        c.close()
        return result[0]
    else:
        c.close()
        return False

def strava_check_create_tables():
    """ Create tables for the database, these should always be up to date """
    conn = sqlite3.connect('strava.sqlite')
    c = conn.cursor()
    tables = {
        'version': "CREATE TABLE version (version_field TEXT, version_number INTEGER)",
        'tokens': "CREATE TABLE tokens (user TEXT UNIQUE ON CONFLICT REPLACE, token TEXT, refresh TEXT)",
        'athletes': "CREATE TABLE athletes (user TEXT UNIQUE ON CONFLICT REPLACE, strava_id TEXT)",
        'gear': "CREATE TABLE gear (user TEXT UNIQUE ON CONFLICT REPLACE, date INTEGER, gear TEXT)"
    }
    # Go through each table and check if it exists, if it doesn't, run the SQL statement to create it.
    for  table_name, sql_statement in tables.items():
        query = "SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"
        if not c.execute(query, {'table_name': table_name}).fetchone():
            # Run the command.
            c.execute(sql_statement)
            conn.commit()
    c.close()

def strava_insert_athlete(nick, athlete_id):
    """ Insert a user's strava id into the athletes table """
    conn = sqlite3.connect('strava.sqlite')
    c = conn.cursor()
    query = "INSERT INTO athletes VALUES (:user, :strava_id)"
    c.execute(query, {'user': nick, 'strava_id': athlete_id})
    conn.commit()
    c.close()

def strava_insert_gear(nick, gear_date, gear_name):
    """ Insert a user's gear and date into the gear table """
    conn = sqlite3.connect('strava.sqlite')
    c = conn.cursor()
    query = "INSERT INTO gear VALUES (:user, :date, :gear)"
    c.execute(query, {'user': nick, 'date': gear_date, 'gear': gear_name})
    conn.commit()
    c.close()

def strava_delete_athlete(nick, athlete_id):
    """ Delete a user's strava id from the athletestable """
    conn = sqlite3.connect('strava.sqlite')
    c = conn.cursor()
    query = "DELETE FROM athletes WHERE user = :user AND strava_id = :strava_id"
    c.execute(query, {'user': nick, 'strava_id': athlete_id})
    conn.commit()
    c.close()

def strava_get_athlete(nick):
    """ Get an athlete ID by user """
    #print('get athlete local db')
    conn = sqlite3.connect('strava.sqlite')
    c = conn.cursor()
    query = "SELECT strava_id FROM athletes WHERE UPPER(user) = UPPER(?)"
    result = c.execute(query, [nick]).fetchone()
    if result:
        c.close()
        return result[0]
    else:
        c.close()
        return False

def strava_get_gear_timer(nick):
    """ Get gear date by user """
    conn = sqlite3.connect('strava.sqlite')
    c = conn.cursor()
    query = "SELECT date, gear FROM gear WHERE UPPER(user) = UPPER(?)"
    result = c.execute(query, [nick]).fetchone()
    if result:
        c.close()
        return result[0], result[1]
    else:
        c.close()
        return False

def strava_line_parser(self, e):
    """ Watch every line for a valid strava line """
    url = re.search(
        r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>])*\))+(?:\(([^\s()<>])*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))",
        e.input)
    if url:
        url = url.group(0)
        url_parts = urlparse(url)
        if url_parts[1] == 'www.strava.com' or url_parts[1] == 'app.strava.com':
            ride = re.match(r"^/activities/(\d+)", url_parts[2])
            if ride and ride.group(1):
                recent_ride = strava_get_ride_extended_info(self, ride.group(1))
                if recent_ride:
                    e.output = strava_ride_to_string(recent_ride)
                else:
                    e.output = "Sorry %s, an error has occured attempting to retrieve ride details for %s. They said Ruby was webscale..." % (
                    e.nick, url)
                return e
    else:
        return
strava_line_parser.lineparser = False

def strava_set_athlete(self, e):
    """ Set an athlete's Strava ID. """
    if e.input.isdigit():
        # Insert the user strava id, we should probably validate the user though right?
        if strava_is_valid_user(e.input, True):
            strava_insert_athlete(e.nick, e.input)
            self.irccontext.privmsg(e.nick, "Your Strava ID has been set to %s. Now go play bikes." % (e.input))
        else:
            # Inform the user that the strava id isn't valid.
            self.irccontext.privmsg(e.nick, "Sorry, that is not a valid Strava user.")
    else:
        # Bark at stupid users.
        self.irccontext.privmsg(e.nick, "Usage: !strava set <strava id>")

def substring_after(s, delim):
    return s.partition(delim)[2]

def strava_set_gear_timer(self,e):
    if e.input:
        split_input = e.input.split(' ')
        gear_date = math.trunc(datetime.datetime.strptime(split_input[0], '%m/%d/%Y').timestamp())#.strftime('%m/%d/%Y')
        gear_name = substring_after(e.input, split_input[0])[1:]

        token, refresh = strava_get_token(e.nick)
        valid_token = check_strava_token(self, e.nick, token, refresh)
        if valid_token == True:
            request_json.token = token
            request_json.refresh = refresh
        elif valid_token == "refreshed":
            token, refresh = strava_get_token(e.nick)
            request_json.token = token
            request_json.refresh = refresh
        athlete_id = strava_get_athlete(e.nick)
        bikeId = ''
        if athlete_id:
            athlete_info = strava_get_athlete_info(athlete_id)
            if not athlete_info:
                self.irccontext.privmsg(e.nick, "Unable to retrieve your athlete info. You may need to !strava auth")
                return
            for bike in athlete_info['bikes']:
                if bike['name'] == gear_name:
                    bikeId = bike['id']
                    break
        if not bikeId:
            self.irccontext.privmsg(e.nick, "No gear match was found. What games are you playing here?")
            return
        strava_insert_gear(e.nick, gear_date, gear_name)
        self.irccontext.privmsg(e.nick, "Your Strava gear timer has been set to %s. Now go play bikes." % (e.input))
    else:
        self.irccontext.privmsg(e.nick, "Please use the correct format. <date> <bike name> EXAMPLE: 12/30/2024 The Big Beast NOTE: The name much match EXACTLY")

def strava_reset_athlete(self, e):
    """ Resets an athlete's Strava ID. """
    athlete_id = strava_get_athlete(e.nick)
    if athlete_id:
        strava_delete_athlete(e.nick, athlete_id)
        self.irccontext.privmsg(e.nick, "Your Strava ID has been reset, but remember, if it's not on Strava, it didn't happen.")
    else:
        self.irccontext.privmsg(e.nick, "You don't even have a Strava ID set, why would you want to reset it?")

def strava(self, e):
    strava_id = strava_get_athlete(e.nick)
    # set the token for the current user
    #token, refresh = strava_get_token(e.nick)
    if e.input:
        athlete_id = strava_get_athlete(e.input)
        if athlete_id:
            try:
                # set the token for the provided user, if we have it
                token, refresh = strava_get_token(e.input)
                valid_token = check_strava_token(self, e.input, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(e.input)
                    request_json.token = token
                    request_json.refresh = refresh
                if strava_is_valid_user(athlete_id):
                    # Process a last ride request for a specific strava id.
                    rides_response = request_json("https://www.strava.com/api/v3/athletes/%s/activities?per_page=1" % athlete_id)
                    e.output = strava_extract_latest_ride(self, rides_response, e, athlete_id)
                else:
                    e.output = "Sorry, that is not a valid Strava user."
            except urllib.error.URLError as err:
                if err.code == 429:
                    e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (e.input)
                else:
                    e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (e.input)
        elif e.input.isdigit():
            try:
                # set the token for the provided user, if we have it
                token, refresh = strava_get_token(e.nick)
                valid_token = check_strava_token(self, e.nick, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(e.nick)
                    request_json.token = token
                    request_json.refresh = refresh

                rides_response = request_json("https://www.strava.com/api/v3/activities/%s" % e.input)
                if rides_response:
                    e.output = strava_extract_latest_ride(self, rides_response, e, e.nick, True)
                else:
                    raise Exception('response empty')
            except urllib.error.URLError as err:
                if err.code == 429:
                    e.output = "Unable to retrieve activity: %s. The user may need to do: !strava auth Too many API requests" % (e.input)
                else:
                    e.output = "Unable to retrieve activity: %s. The user may need to do: !strava auth" % (e.input)
            except:
                e.output = "Unable to retrieve activity: %s. The user may need to do: !strava auth" % (e.input)
        else:
            # We still have some sort of string, but it isn't numberic.
            e.output = "Sorry, %s is not a valid Strava ID." % (e.input)
    elif strava_id:
        try:
            if strava_is_valid_user(strava_id):
                # Process the last ride for the current strava id.
                
                # set the token for the provided user, if we have it
                if (e.input == ''):
                    username = e.nick
                else:
                    username = e.input
                token, refresh = strava_get_token(username)
                valid_token = check_strava_token(self, username, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(username)
                    request_json.token = token
                    request_json.refresh = refresh
                rides_response = request_json("https://www.strava.com/api/v3/athletes/%s/activities?per_page=1" % strava_id)
                e.output = strava_extract_latest_ride(self, rides_response, e, strava_id)
            else:
                e.output = "Sorry, that is not a valid Strava user."
        except urllib.error.URLError as err:
            if err.code == 429:
                e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (strava_id)
            else:
                e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (strava_id)
    else:
        e.output = "Sorry %s, you don't have a Strava ID setup yet, please use the !strava auth command. Remember, if it's not on Strava, it didn't happen." % (e.nick)
    return e

def strava_ftp(self, e):
    strava_id = strava_get_athlete(e.nick)
    # set the token for the current user
    #token, refresh = strava_get_token(e.nick)
    if not e.input:
        e.input = ''
    if e.input:
        athlete_id = strava_get_athlete(e.input)
        if athlete_id:
            try:
                # set the token for the provided user, if we have it
                token, refresh = strava_get_token(e.input)
                valid_token = check_strava_token(self, e.input, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(e.input)
                    request_json.token = token
                    request_json.refresh = refresh
                if strava_is_valid_user(athlete_id):
                    # Process a last ride request for a specific strava id.
                    rides_response = request_json("https://www.strava.com/api/v3/athlete")
                    if rides_response['ftp'] == None or rides_response['ftp'] == 0:
                        e.output = f"No FTP was found for {e.input}"
                    elif e.nick != athlete_id:
                        e.output = f"Wow, {e.input} has a FTP of {rides_response['ftp']} watts. {e.nick}, aren't you jealous?"
                    else:
                        e.output = f"{e.input}, your FTP is only {rides_response['ftp']} watts. Time to harden the fuck up!"
                else:
                    e.output = "Sorry, that is not a valid Strava user."
            except urllib.error.URLError as err:
                if err.code == 429:
                    e.output = "Unable to retrieve FTP from Strava ID: %s. Too many API requests" % (e.input)
                else:
                    e.output = "Unable to retrieve FTP from Strava ID: %s. The user may need to do: !strava auth" % (e.input)
        else:
            # We still have some sort of string, but it isn't numberic.
            e.output = "Sorry, %s is not a valid Strava ID." % (e.input)
    elif strava_id:
        try:
            if strava_is_valid_user(strava_id):
                # Process the last ride for the current strava id.
                
                # set the token for the provided user, if we have it
                if (e.input == ''):
                    username = e.nick
                else:
                    username = e.input
                token, refresh = strava_get_token(username)
                valid_token = check_strava_token(self, username, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(username)
                    request_json.token = token
                    request_json.refresh = refresh
                #else:
                #    request_json.token = self.botconfig["APIkeys"]["stravaToken"]
                rides_response = request_json("https://www.strava.com/api/v3/athlete")
                if rides_response['ftp'] == None or rides_response['ftp'] == 0:
                    e.output = f"No FTP was found for {e.input}"
                elif e.nick != username:
                    e.output = f"Wow, {username} has a FTP of {rides_response['ftp']} watts. {e.nick}, aren't you jealous?"
                else:
                    e.output = f"{username}, your FTP is only {rides_response['ftp']} watts. Time to harden the fuck up!"
            else:
                e.output = "Sorry, that is not a valid Strava user."
        except urllib.error.URLError as err:
            if err.code == 429:
                e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (strava_id)
            else:
                e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (strava_id)
    else:
        e.output = "Sorry %s, you don't have a Strava ID setup yet, please use the !strava auth command. Remember, if it's not on Strava, it didn't happen." % (e.nick)
    return e
strava_ftp.command = "!ftp"
strava_ftp.helptext = "Shows the users FTP. 8====D"

def strava_compare(self, e):
    if not e.input:
        e.input = ''
    participants = e.input.split(' ')
    if len(participants) > 1 or (participants[0].lower() != e.nick.lower() and participants[0] != ''):
        participant_stats_list = []
        if len(participants) == 1:
            participants.append(e.nick)
        for participant in participants:
            e.input = participant
            #check for valid name
            athlete_id = strava_get_athlete(e.input)
            if athlete_id:
                participant_stats = strava_ytd(self, e, True)
                if participant_stats == None:
                    return f"I have no record of {participant}. use <!strava authorize> for help"
                else:
                    stats = UserStats(participant, 
                                        participant_stats['ytd_ride_totals']['count'], 
                                        participant_stats['ytd_ride_totals']['distance'],
                                        participant_stats['ytd_ride_totals']['elevation_gain'],
                                        participant_stats['ytd_ride_totals']['moving_time'],
                                        participant_stats['ytd_ride_totals']['elapsed_time'])
                    participant_stats_list.append(stats)
            else:
                e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (e.input)
                return e

        for participant in participant_stats_list:
            et = datetime.timedelta(seconds=float(participant.elapsed_time))
            elapsedTime = "{:02}h:{:02}m".format((et.days*24)+et.seconds//3600, (et.seconds//60)%60)
            mt = datetime.timedelta(seconds=float(participant.moving_time))
            movingTime = "{:02}h:{:02}m".format((mt.days*24)+mt.seconds//3600, (mt.seconds//60)%60)
            it = datetime.timedelta(seconds=float(participant.elapsed_time - participant.moving_time))
            idleTime = "{:02}h:{:02}m".format((it.days*24)+it.seconds//3600, (it.seconds//60)%60)
            e.output += f"{participant.name}'s Activities: {participant.count} | Distance: {math.trunc(strava_convert_meters_to_miles(participant.distance))} mi | Elevation: {math.trunc(strava_convert_meters_to_feet(participant.elevation_gain))} ft | Moving Time: {movingTime} | Elapsed Time: {elapsedTime} | Sight-seeing: {idleTime}\n"
        
        participant_stats_list_sorted = sorted(participant_stats_list, key=lambda x: x.distance, reverse=True)
        #support for more than two compare nicks
        athlete = 0
        for participant in participant_stats_list_sorted:
            if athlete == 0:
                athlete += 1
                e.output += f"{participant.name} is winning with: {math.trunc(strava_convert_meters_to_miles(participant.distance))} miles"
            else:
                athlete += 1
                e.output += f" | That's {math.trunc(strava_convert_meters_to_miles((participant_stats_list_sorted[0].distance - participant.distance)))} miles more than {participant.name}"
        
        #elevation winner
        athlete = 0
        participant_stats_list_sorted = sorted(participant_stats_list, key=lambda x: x.elevation_gain, reverse=True)
        for participant in participant_stats_list_sorted:
            if athlete == 0:
                athlete += 1
                e.output += f"\n{participant.name} is winning with: {math.trunc(strava_convert_meters_to_feet(participant.elevation_gain))} feet"
            else:
                athlete += 1
                e.output += f" | That's {math.trunc(strava_convert_meters_to_feet((participant_stats_list_sorted[0].elevation_gain - participant.elevation_gain)))} feet more than {participant.name}"
        
        return e
        
    elif participants[0] == '' or participants[0].lower() == e.nick.lower():
        e.output = "Sorry %s, You need something to compare it to. At the very least !compare someothernick" % (e.nick)
        return e
strava_compare.command = "!compare"
strava_compare.helptext = "Usage: !compare nick1 nick2. Compares users year to date stats."

def strava_ytd(self, e, return_response = False):
    strava_id = strava_get_athlete(e.nick)
    # set the token for the current user
    #token, refresh = strava_get_token(e.nick)
    if not e.input:
        e.input = ''

    if e.input:
        athlete_id = strava_get_athlete(e.input)
        if athlete_id:
            try:
                # set the token for the provided user, if we have it
                token, refresh = strava_get_token(e.input)
                valid_token = check_strava_token(self, e.input, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(e.input)
                    request_json.token = token
                    request_json.refresh = refresh
                if strava_is_valid_user(athlete_id):
                    # Process a last ride request for a specific strava id.
                    stats_response = request_json("https://www.strava.com/api/v3/athletes/%s/stats" % athlete_id)
                    if return_response:
                        return stats_response
                    else:
                        e.output = strava_extract_ytd_stats(self, stats_response, e, athlete_id)
                else:
                    e.output = "Sorry, that is not a valid Strava user."
            except urllib.error.URLError as err:
                if err.code == 429:
                    e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (e.input)
                else:
                    e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (e.input)
        else:
            # We still have some sort of string, but it isn't numberic.
            e.output = "Sorry, %s is not a valid Strava ID." % (e.input)
    elif strava_id:
        try:
            if strava_is_valid_user(strava_id):
                # Process the last ride for the current strava id.
                
                # set the token for the provided user, if we have it
                if (e.input == ''):
                    username = e.nick
                else:
                    username = e.input
                token, refresh = strava_get_token(username)
                valid_token = check_strava_token(self, username, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(username)
                    request_json.token = token
                    request_json.refresh = refresh
                stats_response = request_json("https://www.strava.com/api/v3/athletes/%s/stats" % strava_id)
                if return_response:
                    return stats_response
                else:
                    e.output = strava_extract_ytd_stats(self, stats_response, e, strava_id)
            else:
                e.output = "Sorry, that is not a valid Strava user."
        except urllib.error.URLError as err:
            if err.code == 429:
                e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (username)
            else:
                e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (username)
    else:
        e.output = "Sorry %s, you don't have a Strava ID setup yet, please use the !strava auth command. Remember, if it's not on Strava, it didn't happen." % (e.nick)
    return e

def strava_inside(self, e):
    strava_id = strava_get_athlete(e.nick)
    # set the token for the current user
    #token, refresh = strava_get_token(e.nick)
    if not e.input:
        e.input = ''
    #return e
    #length of time to search
    search_history_timestamp = datetime.datetime.now() - datetime.timedelta(days=21, hours=0)
    search_history_timestamp = search_history_timestamp.timestamp()
    if e.input:
        athlete_id = strava_get_athlete(e.input)
        if athlete_id:
            try:
                username = e.input
                # set the token for the provided user, if we have it
                token, refresh = strava_get_token(e.input)
                valid_token = check_strava_token(self, e.input, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(e.input)
                    request_json.token = token
                    request_json.refresh = refresh
                if strava_is_valid_user(athlete_id):
                    # Process a last ride request for a specific strava id.
                    stats_response = request_json(f'https://www.strava.com/api/v3/athletes/{athlete_id}/activities?per_page=200&after={search_history_timestamp}')
                    #stats_response = request_json("https://dylix.org/test.json")
                    stats_response = sorted(stats_response, key=lambda k: k['start_date'], reverse=True)
                    e.output = strava_extract_inside(self, stats_response, e, athlete_id, username)
                else:
                    e.output = "Sorry, that is not a valid Strava user."
            except urllib.error.URLError as err:
                if err.code == 429:
                    e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (e.input)
                else:
                    e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (e.input)
        else:
            # We still have some sort of string, but it isn't numberic.
            e.output = "Sorry, %s is not a valid Strava ID." % (e.input)
    elif strava_id:
        try:
            if strava_is_valid_user(strava_id):
                # Process the last ride for the current strava id.
                
                # set the token for the provided user, if we have it
                if (e.input == ''):
                    username = e.nick
                else:
                    username = e.input
                token, refresh = strava_get_token(username)
                valid_token = check_strava_token(self, username, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(username)
                    request_json.token = token
                    request_json.refresh = refresh
                stats_response = request_json(f'https://www.strava.com/api/v3/athletes/{strava_id}/activities?per_page=200&after={search_history_timestamp}')
                #stats_response = request_json("https://dylix.org/test.json")
                stats_response = sorted(stats_response, key=lambda k: k['start_date'], reverse=True)
                e.output = strava_extract_inside(self, stats_response, e, strava_id, username)
            else:
                e.output = "Sorry, that is not a valid Strava user."
        except urllib.error.URLError as err:
            if err.code == 429:
                e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (strava_id)
            else:
                e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (strava_id)
    else:
        e.output = "Sorry %s, you don't have a Strava ID setup yet, please use the !strava auth command. Remember, if it's not on Strava, it didn't happen." % (e.nick)
    return e

def strava_outside(self, e):
    strava_id = strava_get_athlete(e.nick)
    # set the token for the current user
    #token, refresh = strava_get_token(e.nick)
    if not e.input:
        e.input = ''
    #return e
    #length of time to search
    search_history_timestamp = datetime.datetime.now() - datetime.timedelta(days=21, hours=0)
    search_history_timestamp = search_history_timestamp.timestamp()
    if e.input:
        athlete_id = strava_get_athlete(e.input)
        if athlete_id:
            try:
                username = e.input
                # set the token for the provided user, if we have it
                token, refresh = strava_get_token(e.input)
                valid_token = check_strava_token(self, e.input, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(e.input)
                    request_json.token = token
                    request_json.refresh = refresh
                if strava_is_valid_user(athlete_id):
                    # Process a last ride request for a specific strava id.
                    stats_response = request_json(f'https://www.strava.com/api/v3/athletes/{athlete_id}/activities?per_page=200&after={search_history_timestamp}')
                    #stats_response = request_json("https://dylix.org/test.json")
                    stats_response = sorted(stats_response, key=lambda k: k['start_date'], reverse=True)
                    e.output = strava_extract_outside(self, stats_response, e, athlete_id, username)
                else:
                    e.output = "Sorry, that is not a valid Strava user."
            except urllib.error.URLError as err:
                if err.code == 429:
                    e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (e.input)
                else:
                    e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (e.input)
        else:
            # We still have some sort of string, but it isn't numberic.
            e.output = "Sorry, %s is not a valid Strava ID." % (e.input)
    elif strava_id:
        try:
            if strava_is_valid_user(strava_id):
                # Process the last ride for the current strava id.
                
                # set the token for the provided user, if we have it
                if (e.input == ''):
                    username = e.nick
                else:
                    username = e.input
                token, refresh = strava_get_token(username)
                valid_token = check_strava_token(self, username, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(username)
                    request_json.token = token
                    request_json.refresh = refresh
                stats_response = request_json(f'https://www.strava.com/api/v3/athletes/{strava_id}/activities?per_page=200&after={search_history_timestamp}')
                #stats_response = request_json("https://dylix.org/test.json")
                stats_response = sorted(stats_response, key=lambda k: k['start_date'], reverse=True)
                e.output = strava_extract_outside(self, stats_response, e, strava_id, username)
            else:
                e.output = "Sorry, that is not a valid Strava user."
        except urllib.error.URLError as err:
            if err.code == 429:
                e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (strava_id)
            else:
                e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (strava_id)
    else:
        e.output = "Sorry %s, you don't have a Strava ID setup yet, please use the !strava auth command. Remember, if it's not on Strava, it didn't happen." % (e.nick)
    return e

def strava_gear_timer(self, e):
    strava_id = strava_get_athlete(e.nick)
    # set the token for the current user
    if not e.input:
        e.input = ''

    if e.input:
        athlete_id = strava_get_athlete(e.input)
        try:
            gear_date, gear_name = strava_get_gear_timer(e.input)
        except:
            e.output = "Sorry, %s, %s does not have any timers on gear set. User may need to !strava settimer" % (e.nick, e.input)
            return e
        if athlete_id:
            try:
                username = e.input
                # set the token for the provided user, if we have it
                token, refresh = strava_get_token(e.input)
                valid_token = check_strava_token(self, e.input, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(e.input)
                    request_json.token = token
                    request_json.refresh = refresh
                if strava_is_valid_user(athlete_id):
                    # Process a last ride request for a specific strava id.
                    stats_response = request_json(f'https://www.strava.com/api/v3/athletes/{athlete_id}/activities?per_page=200&after={gear_date}')
                    #stats_response = request_json("https://dylix.org/test.json")
                    stats_response = sorted(stats_response, key=lambda k: k['start_date'], reverse=True)
                    e.output = strava_extract_gear_timer(self, stats_response, e, athlete_id, username, gear_date, gear_name)
                else:
                    e.output = "Sorry, that is not a valid Strava user."
            except urllib.error.URLError as err:
                if err.code == 429:
                    e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (e.input)
                else:
                    e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (e.input)
        else:
            # We still have some sort of string, but it isn't numberic.
            e.output = "Sorry, %s is not a valid Strava ID." % (e.input)
    elif strava_id:
        try:
            if strava_is_valid_user(strava_id):
                # Process the last ride for the current strava id.
                
                # set the token for the provided user, if we have it
                if (e.input == ''):
                    username = e.nick
                else:
                    username = e.input
                try:
                    gear_date, gear_name = strava_get_gear_timer(username)
                except:
                    e.output = "Sorry, %s, you don't have any timers on your gear set. You may need to !strava settimer" % (username)
                    return e
                token, refresh = strava_get_token(username)
                valid_token = check_strava_token(self, username, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(username)
                    request_json.token = token
                    request_json.refresh = refresh
                stats_response = request_json(f'https://www.strava.com/api/v3/athletes/{strava_id}/activities?per_page=200&after={gear_date}')
                #stats_response = request_json("https://dylix.org/test.json")
                stats_response = sorted(stats_response, key=lambda k: k['start_date'], reverse=True)
                e.output = strava_extract_gear_timer(self, stats_response, e, strava_id, username, gear_date, gear_name)
            else:
                e.output = "Sorry, that is not a valid Strava user."
        except urllib.error.URLError as err:
            if err.code == 429:
                e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (strava_id)
            else:
                e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (strava_id)
    else:
        e.output = "Sorry %s, you don't have a Strava ID setup yet, please use the !strava auth command. Remember, if it's not on Strava, it didn't happen." % (e.nick)
    return e

def strava_weekly(self, e):
    strava_id = strava_get_athlete(e.nick)
    # set the token for the current user
    #token, refresh = strava_get_token(e.nick)
    if not e.input:
        e.input = ''
    #return e
    #length of time to search
    
    try:
        d = datetime.datetime.today().weekday()
        last_monday = datetime.datetime.today() + datetime.timedelta(weeks=-1, days=(7-d)%7)
        last_monday = datetime.datetime.combine(last_monday, datetime.datetime.min.time())
        last_monday_timestamp = last_monday.timestamp()
    except Exception as err:
        e.output = str(err)
        return e

    
    if e.input:
        athlete_id = strava_get_athlete(e.input)
        if athlete_id:
            try:
                username = e.input
                # set the token for the provided user, if we have it
                token, refresh = strava_get_token(e.input)
                valid_token = check_strava_token(self, e.input, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(e.input)
                    request_json.token = token
                    request_json.refresh = refresh
                if strava_is_valid_user(athlete_id):
                    # Process a last ride request for a specific strava id.
                    stats_response = request_json(f'https://www.strava.com/api/v3/athletes/{athlete_id}/activities?per_page=200&after={last_monday_timestamp}')
                    #stats_response = request_json("https://dylix.org/test.json")
                    stats_response = sorted(stats_response, key=lambda k: k['start_date'], reverse=True)
                    e.output = strava_extract_weekly(self, stats_response, e, athlete_id, username)
                else:
                    e.output = "Sorry, that is not a valid Strava user."
            except urllib.error.URLError as err:
                if err.code == 429:
                    e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (e.input)
                else:
                    e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (e.input)
        else:
            # We still have some sort of string, but it isn't numberic.
            e.output = "Sorry, %s is not a valid Strava ID." % (e.input)
    elif strava_id:
        try:
            if strava_is_valid_user(strava_id):
                # Process the last ride for the current strava id.
                
                # set the token for the provided user, if we have it
                if (e.input == ''):
                    username = e.nick
                else:
                    username = e.input
                token, refresh = strava_get_token(username)
                valid_token = check_strava_token(self, username, token, refresh)
                if valid_token == True:
                    request_json.token = token
                    request_json.refresh = refresh
                elif valid_token == "refreshed":
                    token, refresh = strava_get_token(username)
                    request_json.token = token
                    request_json.refresh = refresh
                stats_response = request_json(f'https://www.strava.com/api/v3/athletes/{strava_id}/activities?per_page=200&after={last_monday_timestamp}')
                #stats_response = request_json("https://dylix.org/test.json")
                stats_response = sorted(stats_response, key=lambda k: k['start_date'], reverse=True)
                e.output = strava_extract_weekly(self, stats_response, e, strava_id, username)
            else:
                e.output = "Sorry, that is not a valid Strava user."
        except urllib.error.URLError as err:
            if err.code == 429:
                e.output = "Unable to retrieve rides from Strava ID: %s. Too many API requests" % (strava_id)
            else:
                e.output = "Unable to retrieve rides from Strava ID: %s. The user may need to do: !strava auth" % (strava_id)
    else:
        e.output = "Sorry %s, you don't have a Strava ID setup yet, please use the !strava auth command. Remember, if it's not on Strava, it didn't happen." % (e.nick)
    return e

# ==== begin beardedwizard
def strava_parent(self, e):
    strava_command_handler(self, e)
    return e
strava_parent.command = "!strava"
strava_parent.helptext = "Fetch last ride: \"!strava [optional nick]\", Sets a timer for certain gear. Useful for power meter battery life: \"!strava settimer 12/23/2024 StagesBike\", Allow the bot to read your rides: \"!strava auth\", Reset your ID: \"!strava reset\""

def strava_help(self, e):
    e.output += strava_parent.helptext
    return e

def strava_command_handler(self, e):
    arg_offset = 0
    val_offset = 1
    function = None

    arg_function_dict = {'auth': strava_oauth_exchange, 'authorize': strava_oath_code, 'compare': strava_compare, 'ftp': strava_ftp, 'get': strava, # DVQ SAID THIS IS DUMB 'set': strava_set_athlete, 
                         'settimer': strava_set_gear_timer, 'timer': strava_gear_timer, 'reset': strava_reset_athlete, 'inside': strava_inside, 'outside': strava_outside, 
                         'weekly': strava_weekly, 'ytd': strava_ytd, 'help': strava_help}
    arg_list = list(arg_function_dict.keys())

    # EX: "set 123456"
    words = e.input.split()

    # There is something in input
    # EX: "achievements 12345"
    if arg_is_present(words):
        if is_known_arg(words, arg_list):
            # Always clean the arg even if no value is present, patch strava* functions to handle None for e.input
            # EX: "12345" or None
            e.input = clean_arg_from_input(e.input)

        try:
            function = arg_function_dict[words[arg_offset]]
            self.logger.debug(
            "Calling " + function.__name__ + " with e.input of: " + ''.join('none' if e.input is None else e.input))
            function(self, e)
            return e
        except KeyError:
            pass

    # There are no args or only unknown args. We fall through from the exception above
    # EX: "" or "beardedw1zard"
    function = arg_function_dict['get']
    self.logger.debug("Calling " + function.__name__ + " with e.input of: " + ''.join('none' if e.input is None else e.input))
    function(self, e)

    return e

def arg_is_present(words):
    return len(words)

def is_known_arg(args, known_args):
    results = [arg for arg in args if arg in known_args]
    if len(results):
        return 1
    return 0

def clean_arg_from_input(string):
    if len(string.split()) > 1:
        return ' '.join(string.split()[1:])
    return
# ==== end beardedwizard

def strava_extract_latest_ride(self, response, e, athlete_id=None, single=False):
    """ Grab the latest ride from a list of rides and gather some statistics about it """
    if response:
        if single:
            recent_ride = response
        else:
            recent_ride = response[0]
        if recent_ride:
            return strava_ride_to_string(recent_ride, athlete_id)
        else:
            return "Sorry %s, an error has occured attempting to retrieve the most recent ride's details. They said Ruby was webscale..." % (e.nick)
    else:
        return "Sorry %s, no rides have been recorded yet. You may need to run '!strava auth' Remember, if it's not on Strava, it didn't happen." % (e.nick)

def strava_extract_ytd_stats(self, response, e, athlete_id=None):
    """ Grab the users statistics"""
    if response:
        ytd_ride_totals = response['ytd_ride_totals']
        if ytd_ride_totals:
            if athlete_id:
                athlete_info = strava_get_athlete_info(athlete_id)
                try:
                    measurement_pref = athlete_info['measurement_preference']
                except:
                    measurement_pref = None
            else:
                measurement_pref = None
                athlete_info = None

            et = datetime.timedelta(seconds=float(ytd_ride_totals['elapsed_time']))
            elapsedTime = "{:02}h:{:02}m".format((et.days*24)+et.seconds//3600, (et.seconds//60)%60)
            mt = datetime.timedelta(seconds=float(ytd_ride_totals['moving_time']))
            movingTime = "{:02}h:{:02}m".format((mt.days*24)+mt.seconds//3600, (mt.seconds//60)%60)
            it = datetime.timedelta(seconds=float(ytd_ride_totals['elapsed_time'] - ytd_ride_totals['moving_time']))
            idleTime = "{:02}h:{:02}m".format((it.days*24)+it.seconds//3600, str((it.seconds//60)%60))
            
            if measurement_pref == "feet":
                return f"Activities: {ytd_ride_totals['count']} | Distance: {math.trunc(strava_convert_meters_to_miles(ytd_ride_totals['distance']))} mi | Elevation: {math.trunc(strava_convert_meters_to_feet(ytd_ride_totals['elevation_gain']))} ft | Moving Time: {movingTime} | Elapsed Time: {elapsedTime} | Sight-seeing: {idleTime}"
            else:
                return f"Activities: {ytd_ride_totals['count']} | Distance: {ytd_ride_totals['distance'] / 1000} km | Elevation: {ytd_ride_totals['elevation_gain']} meters | Moving Time: {movingTime} | Elapsed Time: {elapsedTime} | Sight-seeing: {idleTime}"
            
        else:
            return "Sorry %s, an error has occured attempting to retrieve year to date stats" % (e.nick)
    else:
        return "Sorry %s, stats were available yet. You may need to run '!strava auth' Remember, if it's not on Strava, it didn't happen." % (e.nick)

def strava_extract_inside(self, response, e, athlete_id=None, username=None):
    if response:
        for activity in response:
            if activity['type'] == 'VirtualRide':
                inside_ride_days = datetime.datetime.utcnow() - datetime.datetime.strptime(activity['start_date'],'%Y-%m-%dT%H:%M:%SZ') #2024-01-18T18:28:07Z
                days, seconds = inside_ride_days.days, inside_ride_days.seconds
                
                total_hours = days * 24 + seconds // 3600
                hours = seconds // 3600
                if days < 1:
                    if hours == 1:
                        inside_time = f"{hours} hour ago"
                    else:
                        inside_time = f"{hours} hours ago"
                else:
                    if days == 1:
                        if hours == 1:
                            inside_time = f"{days} day and {hours} hour ago"
                        else:
                            inside_time = f"{days} day and {hours} hours ago"
                    else:
                        if hours == 1:
                            inside_time = f"{days} days and {hours} hour ago"
                        else:
                            inside_time = f"{days} days and {hours} hours ago"

                return f"{username} last rode inside {inside_time}\n{strava_ride_to_string(activity, athlete_id)}"
        return f"{username} hasn't ridden inside in the last 21 days. Time to harden the fuck up."
    else:
        return "Sorry %s, no stats were available yet. You may need to run '!strava auth' Remember, if it's not on Strava, it didn't happen." % (e.nick)

def strava_extract_outside(self, response, e, athlete_id=None, username=None):
    if response:
        for activity in response:
            if activity['type'] == 'Ride' or activity['type'] == 'EBikeRide':
                outside_ride_days = datetime.datetime.utcnow() - datetime.datetime.strptime(activity['start_date'],'%Y-%m-%dT%H:%M:%SZ') #2024-01-18T18:28:07Z
                days, seconds = outside_ride_days.days, outside_ride_days.seconds
                
                total_hours = days * 24 + seconds // 3600
                hours = seconds // 3600
                if days < 1:
                    if hours == 1:
                        outside_time = f"{hours} hour ago"
                    else:
                        outside_time = f"{hours} hours ago"
                else:
                    if days == 1:
                        if hours == 1:
                            outside_time = f"{days} day and {hours} hour ago"
                        else:
                            outside_time = f"{days} day and {hours} hours ago"
                    else:
                        if hours == 1:
                            outside_time = f"{days} days and {hours} hour ago"
                        else:
                            outside_time = f"{days} days and {hours} hours ago"

                return f"{username} last rode outside {outside_time}\n{strava_ride_to_string(activity, athlete_id)}"
        return f"{username} hasn't ridden outside in the last 21 days. Time to harden the fuck up."
    else:
        return "Sorry %s, no stats were available yet. You may need to run '!strava auth' Remember, if it's not on Strava, it didn't happen." % (e.nick)

def strava_extract_gear_timer(self, response, e, athlete_id=None, username=None, gear_date=None, gear_name=None):
    if response:
        bikeId = ''
        num_ride = 0
        elapsed_time = 0
        moving_time = 0
        try:
            gear_date = datetime.datetime.fromtimestamp(gear_date).strftime("%m/%d/%Y")
            athlete_info = strava_get_athlete_info(athlete_id)
            for bike in athlete_info['bikes']:
                if bike['name'] == gear_name:
                    bikeId = bike['id']
                    break
            for activity in response:
                if activity['gear_id'] == bikeId:
                    num_ride += 1
                    elapsed_time += activity['elapsed_time']
                    moving_time += activity['moving_time']
        except Exception as err:
            return str(err)
        
        et = datetime.timedelta(seconds=float(elapsed_time))
        elapsedTime = "{:02}h:{:02}m".format((et.days*24)+et.seconds//3600, (et.seconds//60)%60)
        mt = datetime.timedelta(seconds=float(moving_time))
        movingTime = "{:02}h:{:02}m".format((mt.days*24)+mt.seconds//3600, (mt.seconds//60)%60)
        it = datetime.timedelta(seconds=float(elapsed_time - moving_time))
        idleTime = "{:02}h:{:02}m".format((it.days*24)+it.seconds//3600, str((it.seconds//60)%60))
        
        return f"{username}'s bike \"{gear_name}\" since {gear_date} has {num_ride} rides, with a moving time of {movingTime} and a total time of {elapsedTime}"

    else:
        return f"{username} hasn't logged anytime on this gear. Time to harden the fuck up."

def strava_extract_weekly(self, response, e, athlete_id=None, username=None):
    weekly_elapsed_time = 0
    weekly_moving_time = 0
    weekly_elevation = 0
    weekly_distance = 0
    weekly_activities = 0
    weekly_avg_speed = 0
    if response:
        if athlete_id:
            athlete_info = strava_get_athlete_info(athlete_id)
            try:
                measurement_pref = athlete_info['measurement_preference']
            except:
                measurement_pref = None
        else:
            measurement_pref = None
            athlete_info = None
        for activity in response:
            if activity['type'] == 'Ride' or activity['type'] == 'EBikeRide' or activity['type'] == 'VirtualRide':
                weekly_distance += activity['distance']
                weekly_elevation += activity['total_elevation_gain']
                weekly_elapsed_time += activity['elapsed_time']
                weekly_moving_time += activity['moving_time']
                weekly_activities += 1
                weekly_avg_speed += activity['average_speed']


                #return f"{username} last rode outside {outside_time}\n{strava_ride_to_string(activity, athlete_id)}"
        et = datetime.timedelta(seconds=float(weekly_elapsed_time))
        elapsedTime = "{:02}h:{:02}m".format((et.days*24)+et.seconds//3600, (et.seconds//60)%60)
        mt = datetime.timedelta(seconds=float(weekly_moving_time))
        movingTime = "{:02}h:{:02}m".format((mt.days*24)+mt.seconds//3600, (mt.seconds//60)%60)
        it = datetime.timedelta(seconds=float(weekly_elapsed_time - weekly_moving_time))
        idleTime = "{:02}h:{:02}m".format((it.days*24)+it.seconds//3600, str((it.seconds//60)%60))
        
        weekly_avg_speed = weekly_avg_speed / weekly_activities
        
        if measurement_pref == "feet":
            return f"{username}'s weekly stats | Distance: {math.trunc(strava_convert_meters_to_miles(weekly_distance))} miles | Elevation: {math.trunc(strava_convert_meters_to_feet(weekly_elevation))} feet | Avg Speed: {round(strava_convert_meters_per_second_to_miles_per_hour(weekly_avg_speed), 1)} mph | Moving Time: {movingTime} | Elapsed Time: {elapsedTime} | Sight-seeing Time: {idleTime}"
        else:
            return f"{username}'s weekly stats | Distance: {round(weekly_distance / 1000, 1)} kilometers | Elevation: {math.trunc(round(weekly_elevation, 0))} meters | Avg Speed: {round(float(weekly_avg_speed) * 3.6, 1)} kph | Moving Time:{movingTime} | Elapsed Time: {elapsedTime} | Sight-seeing Time: {idleTime}"
    else:
        return f"{username} hasn't ridden since the begining of the week. Time to harden the fuck up."

def strava_ride_to_string(recent_ride, athlete_id=None):  # if the athlete ID is missing we can default to mph
    # Convert a lot of stuff we need to display the message
    moving_time = str(datetime.timedelta(seconds=recent_ride['moving_time']))
    ride_datetime = time.strptime(recent_ride['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
    time_start = time.strftime("%B %d, %Y at %I:%M %p", ride_datetime)
    # Try to get the average heart rate
    if 'average_heartrate' in recent_ride:
        avg_hr = recent_ride['average_heartrate']
    else:  # Heart not found
        avg_hr = False
    if athlete_id:
        #try catch.. lgee somehow has authed, but doesn't respond with measurement_preference key?! wtaf?
        athlete_info = strava_get_athlete_info(athlete_id)
        try:
            measurement_pref = athlete_info['measurement_preference']
        except:
            measurement_pref = None
    else:
        measurement_pref = None
        athlete_info = None
    if measurement_pref == "feet":
        mph = strava_convert_meters_per_second_to_miles_per_hour(recent_ride['average_speed'])
        miles = strava_convert_meters_to_miles(recent_ride['distance'])
        max_mph = strava_convert_meters_per_second_to_miles_per_hour(recent_ride['max_speed'])
        feet_climbed = strava_convert_meters_to_feet(recent_ride['total_elevation_gain'])
        # Output string
        return_string = "%s on %s (http://www.strava.com/activities/%s)\n" % (recent_ride['name'], time_start, recent_ride['id'])
        return_string += "%s Stats: %s mi in %s | %s mph average / %s mph max | %s feet climbed" % (recent_ride['sport_type'], miles, moving_time, mph, max_mph, int(feet_climbed))
        #× 9/5) + 32
        # ADD Temp
        if 'average_temp' in recent_ride:
            return_string += " | Avg. Temp: %s°F" % (round((recent_ride['average_temp'] * 9/5) + 32))
        # ADD HR
        if avg_hr > 0:
            return_string += " | Avg. HR: %s" % (int(avg_hr))
    else:
        kmh = round(float(recent_ride['average_speed']) * 3.6, 1)  # meters per second to km/h
        km = round(float(recent_ride['distance'] / 1000), 1)  # meters to km
        max_kmh = round(float(recent_ride['max_speed']) * 3.6, 1)  # m/s to km/h
        m_climbed = recent_ride['total_elevation_gain']
        return_string = "%s on %s (http://www.strava.com/activities/%s)\n" % (recent_ride['name'], time_start, recent_ride['id'])
        return_string += "%s Stats: %s km in %s | %s km/h average / %s km/h max | %s meters climbed" % (recent_ride['sport_type'], km, moving_time, kmh, max_kmh, int(m_climbed))
        # ADD TEMP
        if 'average_temp' in recent_ride:
            return_string += " | Avg. Temp: %s°C" % (int(recent_ride['average_temp']))
        # ADD HR
        if avg_hr > 0:
            return_string += " | Avg. HR: %s" % (int(avg_hr))

    # Figure out if we need to add average watts to the string.
    # We are cyclists.. ofcourse we only want the bigger number. weighted watts are dumb though.
    if 'weighted_average_watts' in recent_ride and (int(recent_ride['weighted_average_watts'])) > (int(recent_ride['average_watts'])):
        if recent_ride['device_watts']:
            return_string += " | %s watts avg power (weighted)" % (int(recent_ride['weighted_average_watts']))
        else:
            return_string += " | %s fake watts avg power (weighted)" % (int(recent_ride['weighted_average_watts']))
        if 'weight' in athlete_info:
            if athlete_info['weight'] > 0:
                return_string += " | Watts/KG: %s" % (round(int(recent_ride['weighted_average_watts']) / int(athlete_info['weight']), 2))
        if avg_hr > 0:
            return_string += " | %s watts/bpm" % (round(recent_ride['weighted_average_watts']/avg_hr, 2))
    elif 'average_watts' in recent_ride:
        if recent_ride['device_watts']:
            return_string += " | %s watts average power" % (int(recent_ride['average_watts']))
        else:
            return_string += " | %s fake watts average power" % (int(recent_ride['average_watts']))
        if 'weight' in athlete_info:
            if athlete_info['weight'] > 0:
                return_string += " | Watts/KG: %s" % (round(int(recent_ride['average_watts']) / int(athlete_info['weight']), 2))
        if avg_hr > 0:
            return_string += " | %s watts/bpm" % (round(recent_ride['average_watts']/avg_hr, 2))

    return return_string

def strava_get_athlete_info(athlete_id):
    #print('getting athlete info')
    try:
        #athlete_info = request_json("https://www.strava.com/api/v3/athletes/%s" % athlete_id)
        athlete_info = request_json("https://www.strava.com/api/v3/athlete")
        if athlete_info:
            return athlete_info
    except:
        return None

def strava_get_ride_extended_info(self, ride_id):
    #print('getting extended info')
    """ Get all the details about a ride. """
    try:
        ride_details = request_json("https://www.strava.com/api/v3/activities/%s" % ride_id)
        self.logger.debug("Strava ride details JSON: ({})".format(ride_details))
        if ride_details:
            return ride_details
        else:
            return False
    except urllib.error.URLError:
        return False

def strava_get_ride_efforts(ride_id):
    """ Get all the efforts (segments and their respective performance) from a ride. """
    try:
        response = urllib.request.urlopen("http://www.strava.com/api/v1/rides/%s/efforts" % (ride_id))
        ride_efforts = json.loads(response.read().decode('utf-8'))
        if 'efforts' in ride_efforts:
            return ride_efforts['efforts']
        else:
            return False
    except urllib.error.URLError:
        return False

def strava_get_ride_achievements(ride_id):
    try:
        ride_achievements = list()
        response = urllib.request.urlopen("http://app.strava.com/rides/%s" % (ride_id))
        page_text = response.read().decode('utf-8')
        soup = BeautifulSoup(page_text, "html.parser")
        table = soup.find('table', {'class': 'top-achievements'})
        if table:
            trs = table.findAll('tr')
            if trs:
                for tr in trs:
                    tds = tr.findAll('td')
                    if tds:
                        tx = re.sub('\n', ' ', ''.join(tds[1].findAll(text=True))).strip()
                        ride_achievements.append(tx)
        return ride_achievements
    except urllib.error.URLError:
        return False

def strava_get_ride_distance_since_date(self, athlete_id, begin_date, offset_count=0):
    """ Recursively aggregate all of the ride mileage since the begin_date by using strava's pagination """
    try:
        ride_distance_sum = 0
        response = urllib.request.urlopen("http://app.strava.com/api/v1/rides?date=%s&athleteId=%s&offset=%s" % (
        begin_date, athlete_id, offset_count))
        rides_details = json.loads(response.read().decode('utf-8'))
        if 'rides' in rides_details:
            for ride in rides_details['rides']:
                ride_details = strava_get_ride_extended_info(self, ride['id'])
                if 'distance' in ride_details:
                    ride_distance_sum = ride_distance_sum + strava_convert_meters_to_miles(ride_details['distance'])
            ride_distance_sum = ride_distance_sum + strava_get_ride_distance_since_date(self, athlete_id, begin_date,
                                                                                        offset_count + 50)
        else:
            return ride_distance_sum
    except urllib.error.URLError:
        return 0

def strava_is_valid_user(strava_id, new=False):
    
    """ Checks to see if a strava id is a valid strava user """
    if not new:
        return True
    try:
        print('checking valid user remote')
        response = urllib.request.urlopen("https://strava.com/athletes/%s" % (strava_id))
        if response:
            return True
        else:
            return False
    except urllib.error.URLError:
        return False

def strava_convert_meters_per_second_to_miles_per_hour(mps):
    """ Converts meters per second to miles per hour, who the fuck uses this to measure bike speed? Idiots. """
    mph = 2.23694 * float(mps)
    return round(mph, 1)

def strava_convert_meters_per_hour_to_miles_per_hour(meph):
    """ Convert meters per hour to miles per hour. """
    mph = 0.000621371192 * float(meph)
    return round(mph, 1)

def strava_convert_meters_to_miles(meters):
    """ Convert meters to miles. """
    miles = 0.000621371 * float(meters)
    return round(miles, 1)

def strava_convert_meters_to_feet(meters):
    """ Convert meters to feet. """
    feet = 3.28084 * float(meters)
    return round(feet, 1)

class UserStats:
  def __init__(self, name, count, distance, elevation_gain, moving_time, elapsed_time):
    self.name = name
    self.count = count
    self.distance = distance
    self.elevation_gain = elevation_gain
    self.moving_time = moving_time
    self.elapsed_time = elapsed_time

def sentencify(text):
    adjectives = "befitting, correct, decent, decorous, genteel, proper, polite, respectable, seemly, acceptable, " \
                 "adequate, satisfactory, tolerable, dignified, elegant, gracious, stiff, stuffy, apt, congenial, " \
                 "harmonious, kosher, permitted, intolerable, unacceptable, unsatisfactory, " \
                 "casual, grungy, informal, seedy, shabby, tacky, awkward, ungraceful, " \
                 "agreeable, blessed, congenial, darling, delectable, delicious, delightful, " \
                 "dreamy, dulcet, enjoyable, felicitous, good, grateful, gratifying, heavenly, jolly, luscious, " \
                 "pleasant, palatable, pleasing, pleasurable, pretty, satisfying, savory, sweet, tasty, " \
                 "welcome,  abominable, ghastly, god-awful, hellish, horrid, miserable, wretched, bilious, " \
                 "disgusting, distasteful, obnoxious, offensive, repugnant, repulsive, revulsive, unsavory, " \
                 "vile, yucky, abhorrent, detestable, hateful, boring, dull, " \
                 "flat, insipid, irksome, stale, tedious, displeasing, dissatisfying, depressing, disheartening, " \
                 "dismal, dreary, gloomy, heartbreaking, heartrending, joyless, sad, unhappy, deplorable," \
                 " doleful, dolorous, lamentable, lugubrious, mournful, regrettable, sorrowful, tragic, aggravating, " \
                 "annoying, exasperating, irritating, peeving, perturbing, vexing, forbidding, hostile, intimidating," \
                 " angering, enraging, infuriating, maddening, outraging, rankling, riling, distressing, disturbing, " \
                 "upsetting".split(", ")

    picked_adjective = adjectives[random.randint(0, len(adjectives)-1)]

    if picked_adjective[0] in ["a", "e", "i", "o", "u"]:
        adjective_article = "an"
    else:
        adjective_article = "a"

    ride_synonyms = "drive, spin, turn, joyride, conveyance, passage, transit, transport, twirl, whirl, round, jaunt, " \
                    "orbit, excursion, ramble, expedition, odyssey, trek, journey, voyage,  roll, cruise, meander, stroll".split(", ")
    synonyms_for_ride = ["drive", "journey", "trip", "excursion", "tour", "trek", "cruise", "spin", "expedition", "jaunt", "joyride", "ramble", "outing", "voyage", "travel", "commute", "safari", "pilgrimage", "circuit", "explore", "adventure", "quest", "sally", "traverse", "ramble", "stroll", "wander", "roam", "amble", "saunter", "mosey", "cakewalk", "promenade", "turn", "jaunt", "sail", "proceed", "progress", "march", "move", "gallop", "canter", "trot", "stride", "hike", "march", "waltz", "climb", "ascend", "descend", "glide", "slide", "slip", "coast", "skate", "ski", "cruise", "hover", "swoop", "soar", "plunge", "plod", "shuffle", "saunter", "amble", "trudge", "tread", "stomp", "stroll", "mosey", "meander", "wander", "gallivant", "peregrinate", "wanderlust", "explore", "rove", "hike", "trek", "ramble", "tour", "excursion", "jaunt", "journey", "trip", "voyage", "pilgrimage", "jaunt", "spin", "turn", "whirl", "cycle", "drive", "ride out", "spin", "jaunt", "whiz", "zoom", "blitz", "blast", "dart", "dash", "bolt", "sprint", "gallop", "race", "speed", "hurry", "scamper", "scramble", "scuttle", "hasten", "hurtle", "rush", "tear", "charge", "plunge", "plummet", "dive", "drop", "fall", "descend", "sink", "plod", "march", "trudge", "stomp", "slog", "stumble", "limp", "shuffle", "wade", "amble", "saunter", "stroll", "roam", "ramble", "meander", "wander", "mosey", "cruise", "sail", "glide", "soar", "fly", "drift", "coast", "hover", "slip", "slide", "skate", "ski", "slalom", "plow", "ride on", "motor", "travel", "commute", "trek", "hike", "journey", "venture", "explore", "quest", "search", "hunt", "prowl", "patrol", "scout", "foray", "sally", "stint", "outgoing", "course", "circumnavigate", "globe-trot"]

    #picked_ride = ride_synonyms[random.randint(0, len(ride_synonyms)-1)]
    picked_ride = synonyms_for_ride[random.randint(0, len(synonyms_for_ride)-1)]


    touch_synonyms = "bit, crumb, dab, dram, driblet, glimmer, hint, lick, little, tad, nip, ounce, " \
                     "ray, shade, shadow, shred, smell, smidgen, speck, splash, spot, sprinkling, trace, " \
                     "iota, semblance, grain, dash, drop, sliver, part, pinch, morsel, chunk, pile, wad, load, bunch".split(", ")

    synonyms_for_touch = ["feel", "contact", "handle", "grasp", "tap", "stroke", "caress", "pat", "press", "palm", "hold", "manipulate", "fondle", "brush", "nudge", "tickle", "thumb", "tactile", "sense", "reach", "meet", "greet", "connect", "join", "link", "reach out", "make contact", "graze", "glide", "slip", "slide", "come into contact", "run into", "impact", "strike", "smack", "hit", "collide", "clash", "bump", "knock", "nuzzle", "probe", "poke", "prod", "investigate", "explore", "examine", "test", "try", "handle", "grope", "palpate", "thumb", "brush", "pat", "caress", "fondle", "pet", "stroke", "press", "graze", "contact", "tap", "trace", "kiss", "hold", "grip", "clasp", "embrace", "nudge", "tickling", "tickle", "itch", "tingle", "prickle", "pierce", "penetrate", "invade", "tangency", "touchdown", "landing", "adjoin", "border", "abut", "neighboring", "adjacent", "proximate", "close", "near", "approximate", "next to", "beside", "alongside", "by", "with", "within", "outside", "encounter", "experience", "come across", "meet with", "confront", "face", "deal with", "handle", "undergo", "impact", "effect", "influence", "affect", "strike", "hit", "reach", "attain", "arrive", "achieve", "gain", "accomplish", "fulfill", "realize", "sense", "perceive", "discern", "detect", "notice", "recognize", "be in contact", "make contact", "come into contact", "be in touch", "make a connection", "establish a connection", "interact", "interface", "commune", "communicate", "associate", "relate", "link", "unite", "blend", "merge", "fuse", "meld", "intermingle", "intermix", "mix", "interact", "influence", "affect", "impact", "touch upon", "concern", "involve", "cover", "encompass"]

    #picked_touch = touch_synonyms[random.randint(0, len(touch_synonyms)-1)]
    picked_touch = synonyms_for_touch[random.randint(0, len(synonyms_for_touch)-1)]

    if picked_touch[0] in ["a", "e", "i", "o", "u"]:
        touch_article = "an"
    else:
        touch_article = "a"

    last_nouns = "descent, dip, dive, drop, fall, nosedive, plunge, boost, hike, elevation, ascent, rise, climb, " \
                 "effort, pain, labor, grind, sweat, toil, slog, struggle". split(", ")
    synonyms_for_hard_effort = ["struggle", "endeavor", "exertion", "vigorous attempt", "determined work", "strenuous effort", "arduous task", "laborious endeavor", "tough undertaking", "herculean effort", "resolute work", "intense exertion", "concentrated labor", "tenacious effort", "gritty attempt", "sustained labor", "exhaustive work", "rigorous striving", "conscientious endeavor", "forceful labor"]
    #picked_noun = last_nouns[random.randint(0, len(last_nouns)-1)]
    picked_noun = synonyms_for_hard_effort[random.randint(0, len(synonyms_for_hard_effort)-1)]

    generated_sentence = "{} {} {} {} with {} {} of {}".format(adjective_article, picked_adjective, text, picked_ride, touch_article, picked_touch, picked_noun)
    return generated_sentence.title()
    #return "{} {} {} {} with {} {} of {}".format(adjective_article, picked_adjective, text,
    #                                                picked_ride, touch_article, picked_touch, picked_noun)
