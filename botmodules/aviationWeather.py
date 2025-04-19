import urllib.request
import xml.dom.minidom
from metar.Metar import Metar

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
      #e.output = dom.getElementsByTagName('raw_text')[0].childNodes[0].data
      report = Metar(dom.getElementsByTagName('raw_text')[0].childNodes[0].data)
      output = "Weather Report for {}: Time: {} Temperature: {}°C Wind: {} Visibility: {} Cloud Cover: {} Pressure: {} hPa Weather Conditions: {}"
      #e.output = output.format(report.station, report.time, report.temp, report.wind(), report.visibility(), report.sky_conditions(), report.pressure, report.weather)
      e.output = output.format(report.station_id, report.time, report.temp, report.wind(), report.visibility(), report.sky_conditions(), report.press, report.weather)
      return e
  except Exception as e:
      e.output = "Error parsing METAR report: {e}"
      return e
  
metar.command = '!metar'
