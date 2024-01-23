import urllib.request
import xmltodict
import iso8601
import datetime
import string
from bs4 import BeautifulSoup
import json
import random

def call_zwift(self, e):
    # Figure out map information.
    zwift = Zwift()
    current_map = zwift.current_map()
    next_map = zwift.next_map()
    next_timedelta = zwift.next_timedelta()
    
    current_portal_map = zwift.current_portal_map()
    next_portal_map = zwift.next_portal_map()
    monthly_portal_map = zwift.monthly_portal_map()
    next_portal_timedelta = zwift.next_portal_timedelta()

    # Are we asking about a specific map?
    if e.input:
        course = e.input.strip()
        course_datetime = zwift.find_next_map_datetime(course)
        if current_map.upper() == course.upper():
            e.output = '{}, {} is running right now for another {}'.format(
                e.nick,
                string.capwords(current_map),
                Zwift.timedelta_to_string(next_timedelta)
            )
        elif course_datetime:
            e.output = '{}, {} is next scheduled in {}'.format(
                e.nick,
                string.capwords(course),
                Zwift.timedelta_to_string(course_datetime - datetime.datetime.now(datetime.timezone.utc))
            )
        else:
            e.output = '{}, the course \'{}\' has not been scheduled yet.'.format(
                e.nick,
                course
            )
    else:
        # Output what information we can gather.
        if current_map and next_map:
            e.output = '{}, the current map is {}. {} will start in {}\nPortals -> Monthly-> {} || Daily-> {} || {} will start in {}'.format(
                e.nick,
                string.capwords(current_map),
                string.capwords(next_map),
                Zwift.timedelta_to_string(next_timedelta),
                monthly_portal_map,
                current_portal_map,
                next_portal_map,
                Zwift.timedelta_to_string(next_portal_timedelta)
            )
        elif current_map:
            e.output = '{}, the current map is {}'.format(e.nick, current_map)
        elif next_map:
            e.output = '{}, the next map is {} in {}'.format(e.nick, next_map,
                                                             Zwift.timedelta_to_string(next_timedelta))
        else:
            e.output = '{}, I have no clue, try https://whatsonzwift.com'.format(e.nick)

    return e

call_zwift.command = "!zwift"
call_zwift.helptext = 'Current and next course: "!zwift", Next schedule for specific course: "!zwift Watopia"'


class Zwift:
    map_xml = None
    portal_map_xml = None

    zwift_worlds = { "FRANCE" : "FRANCE & PARIS",
                    "MAKURIISLANDS": "MAKURI ISLANDS & NEW YORK",
                    "SCOTLAND": "SCOTLAND & MAKURI ISLANDS",
                    "INNSBRUCK": "INNSBRUCK & RICHMOND",
                    "RICHMOND": "RICHMOND & LONDON",
                    "LONDON": "LONDON & YORKSHIRE"
                    }

    def __init__(self):
        self.load_xml()
        self.load_portal_xml()

    def load_xml(self):
        map_xml = urllib.request.urlopen('https://cdn.zwift.com/gameassets/MapSchedule_v2.xml').read().decode('utf-8')
        self.map_xml = xmltodict.parse(map_xml)

    def load_portal_xml(self):
        portal_map_xml = urllib.request.urlopen('https://cdn.zwift.com/gameassets/PortalRoadSchedule_v1.xml').read().decode('utf-8')
        self.portal_map_xml = xmltodict.parse(portal_map_xml)

    def current(self, now=datetime.datetime.now(datetime.timezone.utc)):
        latest_stamp = None
        current_appointment = None
        for appointment in self.map_xml['MapSchedule']['appointments']['appointment']:
            starts_at = iso8601.parse_date(appointment['@start']).astimezone(datetime.timezone.utc)
            if starts_at <= now and (latest_stamp is None or starts_at >= latest_stamp):
                current_appointment = appointment
                latest_stamp = starts_at
        return current_appointment

    def current_portal(self, now=datetime.datetime.now(datetime.timezone.utc)):
        latest_stamp = None
        current_appointment = None
        for appointment in self.portal_map_xml['PortalRoads']['PortalRoadSchedule']['appointments']['appointment']:
            starts_at = iso8601.parse_date(appointment['@start']).astimezone(datetime.timezone.utc)
            if starts_at <= now and (latest_stamp is None or starts_at >= latest_stamp):
                current_appointment = appointment
                latest_stamp = starts_at
        return current_appointment

    def monthly_portal(self, now=datetime.datetime.now(datetime.timezone.utc)):
        latest_stamp = None
        current_appointment = None
        for appointment in self.portal_map_xml['PortalRoads']['PortalRoadSchedule']['appointments']['appointment']:
            if appointment['@world'] == '10':
                starts_at = iso8601.parse_date(appointment['@start']).astimezone(datetime.timezone.utc)
                month_date = datetime.datetime.combine(datetime.datetime.today(), datetime.datetime.min.time()).astimezone(datetime.timezone.utc).replace(day=1,hour=4,minute=1)
                if starts_at == month_date:
                    current_appointment = appointment
                    latest_stamp = starts_at
        return current_appointment

    def next(self, now=datetime.datetime.now(datetime.timezone.utc)):
        earliest_stamp = None
        next_appointment = None
        for appointment in self.map_xml['MapSchedule']['appointments']['appointment']:
            starts_at = iso8601.parse_date(appointment['@start'])
            if (starts_at > now) and (earliest_stamp is None or starts_at < earliest_stamp):
                next_appointment = appointment
                earliest_stamp = starts_at
        return next_appointment

    def next_portal(self, now=datetime.datetime.now(datetime.timezone.utc)):
        earliest_stamp = None
        next_appointment = None
        for appointment in self.portal_map_xml['PortalRoads']['PortalRoadSchedule']['appointments']['appointment']:
            starts_at = iso8601.parse_date(appointment['@start'])
            if (starts_at > now) and (earliest_stamp is None or starts_at < earliest_stamp):
                next_appointment = appointment
                earliest_stamp = starts_at
        return next_appointment

    def current_map(self):
        current_appointment = self.current()
        if current_appointment['@map']:
            return self.zwift_worlds[current_appointment['@map']]
        else:
            return None

    def current_portal_map(self):
        current_appointment = self.current_portal()
        if current_appointment['@road']:
            for portal in self.portal_map_xml['PortalRoads']['PortalRoadMetadataCollections']['PortalRoadMetadata']:
                if portal['@id'] == current_appointment['@road']:
                    return f"{portal['@name']} ({round(float(portal['@distanceCentimeters'])/160900,2)} miles {round(float(portal['@elevCentimeters'])/30.48,0)} feet)"
        else:
            return None

    def monthly_portal_map(self):
        current_appointment = self.monthly_portal()
        if current_appointment['@road']:
            for portal in self.portal_map_xml['PortalRoads']['PortalRoadMetadataCollections']['PortalRoadMetadata']:
                if portal['@id'] == current_appointment['@road']:
                    return portal['@name']
        else:
            return None

    def next_map(self):
        next_appointment = self.next()
        if next_appointment['@map']:
            return self.zwift_worlds[next_appointment['@map']]
        else:
            return None

    def next_portal_map(self):
        next_appointment = self.next_portal()
        if next_appointment['@road']:
            for portal in self.portal_map_xml['PortalRoads']['PortalRoadMetadataCollections']['PortalRoadMetadata']:
                if portal['@id'] == next_appointment['@road']:
                    return f"{portal['@name']} ({round(float(portal['@distanceCentimeters'])/160900,2)} miles {round(float(portal['@elevCentimeters'])/30.48,0)} feet)"
        else:
            return None

    def next_timedelta(self):
        next_appointment = self.next()
        if next_appointment:
            now = datetime.datetime.now(datetime.timezone.utc)
            return iso8601.parse_date(next_appointment['@start']) - now
        else:
            return None

    def next_portal_timedelta(self):
        next_appointment = self.next_portal()
        if next_appointment:
            now = datetime.datetime.now(datetime.timezone.utc)
            return iso8601.parse_date(next_appointment['@start']) - now
        else:
            return None

    def find_next_map_datetime(self, course, now=datetime.datetime.now(datetime.timezone.utc)):
        course = course.upper()
        earliest_stamp = None
        next_starts_at = None
        for appointment in self.map_xml['MapSchedule']['appointments']['appointment']:
            starts_at = iso8601.parse_date(appointment['@start'])
            if starts_at > now and (earliest_stamp is None or starts_at < earliest_stamp) and appointment['@map'] == course:
                next_starts_at = starts_at
                earliest_stamp = starts_at
        return next_starts_at

    def find_next_portal_map_datetime(self, course, now=datetime.datetime.now(datetime.timezone.utc)):
        course = course.upper()
        earliest_stamp = None
        next_starts_at = None
        for appointment in self.portal_map_xml['PortalRoads']['PortalRoadSchedule']['appointments']['appointment']:
            starts_at = iso8601.parse_date(appointment['@start'])
            if starts_at > now and (earliest_stamp is None or starts_at < earliest_stamp) and appointment['@road'] == course:
                next_starts_at = starts_at
                earliest_stamp = starts_at
        return next_starts_at

    @staticmethod
    def timedelta_to_string(timedelta):
        hours = int(timedelta.seconds / 60 / 60)
        minutes = int((timedelta.seconds / 60) - (hours * 60))
        seconds = int(timedelta.seconds - ((hours * 60 * 60) + (minutes * 60)))
        return '{} days {} hours {} minutes {} seconds'.format(
            int(timedelta.days),
            int(hours),
            int(minutes),
            int(seconds)
        )

#import requests
#from bs4 import BeautifulSoup
#import random
#from datetime import datetime

def zwift_whats_on(self, e):
    combined = ''
    try:
        currentDateTime = datetime.datetime.now()
        month = currentDateTime.strftime("%b").lower()
        year = str(currentDateTime.year)
        url = f"https://zwiftinsider.com/schedule/?grid-list-toggle=grid&month={month}&yr={year}"
        #url = "https://dylix.org/test.html"
        try:            
            page = self.tools["load_html_from_url"](url)
        except urllib.error.HTTPError as err:
            self.logger.exception(f"Exception in zwift_whats_on: {err}")
        soup = page
        print(soup)
        node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day} current-day day-with-date")#.find("span", class_="event-title")
        if node is None:
            node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day} current-day weekend day-with-date")#.find("span", class_="event-title")
        if node is None:
            node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day}  day-with-date")#.find("span", class_="event-title")
        if node is None:
            node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day}  weekend day-with-date")#.find("span", class_="event-title")
        for event_node in node.find_all("span", class_="event-title"):
            combined += f"{event_node.get_text()} & "
        combined = combined[:-3].replace("\n", "")
        maps = combined.split(" & ")
        
        url = "https://dylix.org/zwift/zwift.json"
        request = urllib.request.Request(url)
        response = urllib.request.urlopen(request)
        zwiftRoutes = json.loads(response.read().decode('utf-8'))
        todaysMaps = [x for x in zwiftRoutes if x['World'] == "Watopia" or x['World'] == maps[0] or x['World'] == maps[1] if x['TotalDistance'] > 15]
        randomMapNum = random.randint(0, len(todaysMaps) - 1)
        randomRoute = todaysMaps[randomMapNum]
        combined = f"Todays maps are {combined}"
        combined += f"\nRandom Route -> {randomRoute['World']} - {randomRoute['Name']} -> {randomRoute['TotalDistance']} {randomRoute['TotalElevation']} {randomRoute['TotalDistance']} {randomRoute['TotalElevation']}) / Notes: {randomRoute['Notes']}"
        print(combined)
        
        
        combinedPortal = ''
        #url = f"https://zwiftinsider.com/climb-portal-schedule/?grid-list-toggle=grid&month={month}&yr={year}"
        url = "https://dylix.org/test.html"
        try:            
            page = self.tools["load_html_from_url"](url)
        except urllib.error.HTTPError as err:
            self.logger.exception(f"Exception in zwift_whats_on: {err}")
        soup = page
        print(soup)
        node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day} current-day day-with-date")#.find("span", class_="event-title")
        if node is None:
            node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day} current-day weekend day-with-date")#.find("span", class_="event-title")
        if node is None:
            node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day}  day-with-date")#.find("span", class_="event-title")
        if node is None:
            node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day}  weekend day-with-date")#.find("span", class_="event-title")
        for event_node in node.find_all("span", class_="event-title"):
            combinedPortal += f"{event_node.get_text()} & "
        combinedPortal = combinedPortal[:-3].replace("\n", "")
        maps = combined.split(" & ")
        print(maps)

        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day} current-day day-with-date").find("span", class_="event-title")
        if node is None:
            node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day} current-day weekend day-with-date").find("span", class_="event-title")
        if node is None:
            node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day}  day-with-date").find("span", class_="event-title")
        if node is None:
            node = soup.find("td", class_=f"spiffy-day-{currentDateTime.day}  weekend day-with-date").find("span", class_="event-title")
        row = 0
        for tempnode in node:
            if row % 2 != 1:
                combinedPortal += tempnode.get_text()[len(tempnode.get_text()) // 2:] + " & "
            row += 1
        combinedPortal = combinedPortal.replace("\n", "")
        combinedPortal = combinedPortal[:-3]
        maps = combinedPortal.split(" & ")
        
        
        
        url = "https://zwiftinsider.com/climb-portal-list/"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')
        zwiftPortals = []
        for portRow in soup.select("#wpv-view-layout-96833 figure table tbody tr"):
            i = 0
            zwiftPortalNode = {}
            for col in portRow.select("td"):
                i += 1
                if i == 1:
                    zwiftPortalNode["Title"] = col.get_text()
                elif i == 2:
                    zwiftPortalNode["Length"] = col.get_text()
                elif i == 3:
                    zwiftPortalNode["Elevation"] = col.get_text()
                elif i == 4:
                    zwiftPortalNode["Gradient"] = col.get_text()
            zwiftPortals.append(zwiftPortalNode)
        combined += "::Climb Portals -> "
        mapNum = 0
        for map in maps:
            mapNum += 1
            zwiftPortal = next((x for x in zwiftPortals if map in x["Title"]), None)
            if mapNum == 1:
                combined += f"Watopia: {zwiftPortal['Title']} / {zwiftPortal['LengthMiles']} / {zwiftPortal['ElevationFeet']} / {zwiftPortal['Gradient']} || "
            else:
                combined += f"France: {zwiftPortal['Title']} / {zwiftPortal['LengthMiles']} / {zwiftPortal['ElevationFeet']} / {zwiftPortal['Gradient']}"
    except Exception as ex:
        combined = f"Error has occured fetching the data. {ex}"
    e.output = combined
    return e

zwift_whats_on.command = "!zwift2"
zwift_whats_on.helptext = 'Current and next course: "!zwift", Next schedule for specific course: "!zwift Watopia"'
