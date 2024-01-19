import re, urllib.request, urllib.error, urllib.parse, urllib, json, traceback
from html.entities import name2codepoint as n2cp
from bs4 import BeautifulSoup
import encodings.idna
import datetime
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

def __init__(self):
    google_url.self = self


def set_googleapi(line, nick, self, c):
    google_url.self.botconfig["APIkeys"]["gsearchapi"] = line[11:]
    with open('genmaybot.cfg', 'w') as configfile:
        self.botconfig.write(configfile)
set_googleapi.admincommand = "gsearchapi"

def set_googlecx(line, nick, self, c):
    google_url.self.botconfig["APIkeys"]["gsearchcx"] = line[10:]
    with open('genmaybot.cfg', 'w') as configfile:
        self.botconfig.write(configfile)
set_googlecx.admincommand = "gsearchcx"

def set_shorturlkey(line, nick, self, c):
    google_url.self.botconfig["APIkeys"]["shorturlkey"] = line[12:]
    with open('genmaybot.cfg', 'w') as configfile:
        self.botconfig.write(configfile)
set_shorturlkey.admincommand = "shorturlkey"

def decode_htmlentities(string):
    #decodes things like &amp
    entity_re = re.compile("&(#?)(x?)(\w+);")
    return entity_re.subn(substitute_entity, string)[0]

def insert_newline(original_string):
    interval = 360
    character_to_insert = '\n'
    modified_string = ''
    for i in range(0, len(original_string), interval):
        print("i",i," orig:",len(original_string))
        modified_string += original_string[i:i+interval] + character_to_insert
    return modified_string

def substitute_entity(match):
  try:
    ent = match.group(3)

    if match.group(1) == "#":
        if match.group(2) == '':
            return chr(int(ent))
        elif match.group(2) == 'x':
            return chr(int('0x' + ent, 16))
    else:
        cp = n2cp.get(ent)

        if cp:
            return chr(cp)
        else:
            return match.group()
  except:
    return ""


def remove_html_tags(data):
    #removes all html tags from a given string
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def google_url(searchterm, regexstring):
    searchterm = urllib.parse.quote(searchterm)
    key = google_url.self.botconfig["APIkeys"]["gsearchapi"]
    cx = google_url.self.botconfig["APIkeys"]["gsearchcx"]
    url = 'https://www.googleapis.com/customsearch/v1?key={}&cx={}&q={}'
    url = url.format(key, cx, searchterm)
    
    try:
        request = urllib.request.Request(url, None, {'Referer': 'http://irc.00id.net'})
        response = urllib.request.urlopen(request)
    except urllib.error.HTTPError as err:
        print(err.read())

    results_json = json.loads(response.read().decode('utf-8'))
    results = results_json['items']

    for result in results:
        print(result['link'])
        m = re.search(regexstring, result['link'])
        print(m)
        if (m):
            url = result['link']
            url = url.replace('%25', '%')
            return url
    return


def load_html_from_url(url, readlength="", returnurl=False):
    #print("url:",url)
    url = fixurl(url)
    #print("fixurl:",url)
    opener = urllib.request.build_opener()

    opener.addheaders = [('User-Agent', "Opera/9.10 (YourMom 8.0)")]

    page = None
    pagetmp = opener.open(url)
    if pagetmp.headers['content-type'].find("text") != -1:
        url = pagetmp.geturl()
        if readlength:
            page = pagetmp.read(int(readlength))
        else:
            page = pagetmp.read()
        page = BeautifulSoup(page, features='html.parser')
    opener.close()
    if returnurl:
        return page, url
    return page

def findLatLong(location=""):
    if location.isdigit():
        with open("us-zip-code-latitude-and-longitude.json", "r") as f:
            cities = json.loads(f.read())
        city = [item for item in cities if item['fields']['zip'] == location]
        #print(city['fields']["city"])
        
        try:
            return city[0]['fields']['city'] + ", " + city[0]['fields']['state'], city[0]['fields']['latitude'], city[0]['fields']['longitude'], "US"
        except Exception as e:
            print(e)
            pass
    else:
        with open("city.list.json", "r") as f:
            cities = json.loads(f.read())
    #city = next((item for item in cities if item["name"].lower() == location.split(',')[0].lower()), None)
    city = [item for item in cities if item["name"].lower() == location.split(',')[0].lower()]
    for result in city:
        try:
            if result["state"].lower() == location.split(',')[1].lower().strip():
                city=result
                break
            elif result["country"].lower() == location.split(',')[1].lower().strip():
                city=result
                break
            
        except Exception as e:
            #city=result
            #print("first if ", e)
            break

    #print("before second ", city)
    #print(len(city))
    if len(city) > 5 or not city:
        try:
            city = [item for item in cities if item["name"].lower() == location.rsplit(' ', 1)[0].lower() and item["country"].lower() == location.rsplit(' ', 1)[1].lower()]
        except:
            city = [item for item in cities if item["name"].lower() == location.rsplit(' ', 1)[0].lower() and item["country"] == "US"]
        #print("before not city ", city)
        if not city:
            city = [item for item in cities if item["name"].lower() == location.lower() and item["country"] == "US"]
        for result in city:
            try:
                if result["state"].lower() == location.rsplit(' ', 1)[-1].lower().strip():
                    city=result
                    break
            except Exception as e:
                #city=result
                #print("second if ", e)
                break
    #print("\n\nAfter second ", city)

    if len(city) > 5 or not city:
        city = [item for item in cities if item["name"].lower() == location.rsplit(' ', 1)[0].lower()]
        #print("second list of city ", city)
        for result in city:
            try:
                if result["state"].lower() == location.rsplit(' ', 1)[-1].lower().strip():
                    city=result
                    break
            except Exception as e:
                #print("third if ", e)
                #city=result
                break
    try:
        if (len(city) > 0):
            city=city[0]
    except:
        pass
    if city:
        if (city["country"] == "US"):
            return city["name"] + ", " + city["state"], city["coord"]["lat"], city["coord"]["lon"],city["country"]
        else:
            return city["name"] + ", " + city["country"], city["coord"]["lat"], city["coord"]["lon"],city["country"]
    return None

def shorten_url(url):
    #goo.gl url shortening service, not used directly but used by some commands
  try:
    key = google_url.self.botconfig["APIkeys"]["yourlsAPIkey"]
    values = {'url': url, 'action': 'shorturl', 'format': 'json', 'signature': key}
    data = urllib.parse.urlencode(values)
    data = data.encode('ascii') # data should be bytes
    #headers = {'Content-Type': 'application/json'}
    request_url = "https://dylix.org/yourls/yourls-api.php"
    #req = urllib.request.Request(request_url, values.encode(), headers)
    #url_values = urllib.parse.urlencode(values)
    req = urllib.request.Request(request_url, data)
    #print(req)
    #full_url = request_url + '?' + url_values
    #print(full_url)
    #response = urllib.request.urlopen(full_url)
    response = urllib.request.urlopen(req)
    results = json.loads(response.read().decode('utf-8'))
    shorturl = results['shorturl']
    return shorturl
  except HTTPError as e:
    response_str = e.file.read().decode("utf-8")
    #print(response_str)
    #response = urllib.request.urlopen(full_url)
    #response = urllib.request.urlopen(req)
    results = json.loads(response_str)
    shorturl = results['shorturl']
    return shorturl
  except URLError as e:
    print('We failed to reach a server.')
    print('Reason: ', e.reason)
  except:
    traceback.print_exc()
    return ""


def fixurl(url):
    # turn string into unicode
    if not isinstance(url, str):
        url = url.decode('utf8')

    # parse it
    parsed = urllib.parse.urlsplit(url)

    # divide the netloc further
    hostport = parsed.netloc
    host, colon2, port = hostport.partition(':')

    hostnames = host.split(".")
    tmplist = []

    for tmp in hostnames:
        tmp = encodings.idna.ToASCII(tmp).decode()
        tmplist.append(tmp)
    host = ".".join(tmplist)

    scheme = parsed.scheme

    path = '/'.join(  # could be encoded slashes!
        urllib.parse.quote(urllib.parse.unquote_to_bytes(pce), '')
        for pce in parsed.path.split('/')
    )
    query = urllib.parse.quote(urllib.parse.unquote_to_bytes(parsed.query), '=&?/')
    fragment = urllib.parse.quote(urllib.parse.unquote_to_bytes(parsed.fragment))

    # put it back together
    netloc = ''.join((host, colon2, port))
    return urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))


def prettytimedelta(td):
    seconds = int(td.total_seconds())
    periods = [('year',        60*60*24*365),
               ('month',       60*60*24*30),
               ('day',         60*60*24),
               ('hour',        60*60),
               ('minute',      60),
               ('second',      1)
               ]

    strings = []
    for period_name, period_seconds in periods:
        if seconds > period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            if period_value == 1:
                strings.append("%s %s" % (period_value, period_name))
            else:
                strings.append("%s %ss" % (period_value, period_name))

    return ", ".join(strings)
