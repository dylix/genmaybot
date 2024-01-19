import urllib.request
import xml.dom.minidom

def metar(self, e):
  station = e.input.split(' ')[0]
  if station == '' or station == None:
    e.output = "Please enter a valid weather station. eg: k3u3"
    return e
  #url = 'http://aviationweather.gov/adds/dataserver_current/httpparam?' \
  #+ 'dataSource=metars&requestType=retrieve&format=xml&stationString=' \
  #+ station \
  #+ '&hoursBeforeNow=2&mostRecent=true'
  url = 'https://aviationweather.gov/cgi-bin/data/metar.php?ids=' + station + '&hours=0&order=id%2C-obs&sep=true&format=xml'
  try:
      dom =  xml.dom.minidom.parse(urllib.request.urlopen(url))
      e.output = dom.getElementsByTagName('raw_text')[0].childNodes[0].data
      return e
  except:
      e.output = "Error fetching metar. Invalid station maybe?"
      return e
  
metar.command = '!metar'
