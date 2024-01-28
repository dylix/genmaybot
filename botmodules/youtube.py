import json
import urllib.request
import re
import datetime
from pytube import YouTube
from pytube import Search

def ytinfo(self, e, urlposted=False):
    if urlposted:
        yt = e.input
        if "youtube.com" not in yt and "youtu.be" not in yt:
            return
        yt = re.search("(v=|/)([\w-]+)(&.+|#t=.+|\?t=.+)?$", yt).group(2)
        url = f"https://youtu.be/{yt}"
    else:
        #yt = self.tools['google_url']('site:youtube.com {}'.format(e.input), 'watch\?v=')
        if e.input == '':
            e.output = "Requires a search parameter."
            return e.output
        yt = Search(e.input)
        url = yt.results[0].watch_url

    yt = YouTube(url)
    title = yt.title
    duration = str(datetime.timedelta(seconds = yt.length))
    viewcount = yt.views
    uploader = yt.author
    pubdate = yt.publish_date.strftime("%m/%d/%Y")
    if urlposted:
        e.output = "Youtube: {} :: length: {} - {} views - {} on {}".format(title, duration, viewcount, uploader, pubdate)
    else:
        e.output = "Youtube: {} :: {} :: length: {} - {} views - {} on {}".format(url, title, duration, viewcount, uploader, pubdate)
    return e
ytinfo.command = "!yt"
ytinfo.helptext = """
Usage: !yt <vide title>
Example: !yt cad video
Looks up a given youtube video, and provides information and a link"""

def convert(seconds):
    seconds = seconds % (24 * 3600)
    hour = seconds // 3600
    seconds %= 3600
    minutes = seconds // 60
    seconds %= 60
     
    return "%d:%02d:%02d" % (hour, minutes, seconds)