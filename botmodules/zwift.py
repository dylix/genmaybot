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

    def current(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        latest_stamp = None
        current_appointment = None
        for appointment in self.map_xml['MapSchedule']['appointments']['appointment']:
            starts_at = iso8601.parse_date(appointment['@start']).astimezone(datetime.timezone.utc)
            if starts_at <= now and (latest_stamp is None or starts_at >= latest_stamp):
                current_appointment = appointment
                latest_stamp = starts_at
        return current_appointment

    def current_portal(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        latest_stamp = None
        current_appointment = None
        for appointment in self.portal_map_xml['PortalRoads']['PortalRoadSchedule']['appointments']['appointment']:
            starts_at = iso8601.parse_date(appointment['@start']).astimezone(datetime.timezone.utc)
            if starts_at <= now and (latest_stamp is None or starts_at >= latest_stamp):
                current_appointment = appointment
                latest_stamp = starts_at
        return current_appointment

    def monthly_portal(self):
        now = datetime.datetime.now(datetime.timezone.utc)
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

    def next(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        earliest_stamp = None
        next_appointment = None
        for appointment in self.map_xml['MapSchedule']['appointments']['appointment']:
            starts_at = iso8601.parse_date(appointment['@start'])
            if (starts_at > now) and (earliest_stamp is None or starts_at < earliest_stamp):
                next_appointment = appointment
                earliest_stamp = starts_at
        return next_appointment

    def next_portal(self):
        now = datetime.datetime.now(datetime.timezone.utc)
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
                    return f"{portal['@name']} ({round(float(portal['@distanceCentimeters'])/160900,2)} miles {round(float(portal['@elevCentimeters'])/30.48,0)} feet)"
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

    def find_next_map_datetime(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        course = course.upper()
        earliest_stamp = None
        next_starts_at = None
        for appointment in self.map_xml['MapSchedule']['appointments']['appointment']:
            starts_at = iso8601.parse_date(appointment['@start'])
            if starts_at > now and (earliest_stamp is None or starts_at < earliest_stamp) and appointment['@map'] == course:
                next_starts_at = starts_at
                earliest_stamp = starts_at
        return next_starts_at

    def find_next_portal_map_datetime(self, course):
        now = datetime.datetime.now(datetime.timezone.utc)
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