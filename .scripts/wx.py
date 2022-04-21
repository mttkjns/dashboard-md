#!/usr/bin/env python3

#   this script requests weather and alerts from api.weather.gov and 
#   formats data into markdown for viewing.

from codecs import getreader
import requests
import frontmatter #https://github.com/eyeseast/python-frontmatter
import time
import sys
import datetime
import pytz

# get api key from secrets, passed as an argument
try :
    key = sys.argv[1]
except IndexError :
    sys.exit("No api key provided. Exit.")

def getResponse(url, session) :
    response = session.get(url)
    if response.status_code != 200 :
        print("first request failed, waiting and trying again...")
        time.sleep(5)
        response = session.get(url)
        if response.status_code != 200 :
            appendError(f"Request Failed with error: {response.status_code}")
            print(f"Request for forecast failed with status code {response.status_code}")
            sys.exit()
    return response

def appendError(errorStr) :
    with open('./config/wx_error.md', 'r+') as wxError :
        content = wxError.read()
        wxError.seek(0)
        wxError.write(f"{datetime.datetime.now()}: Location: {wxLocation} Error: {errorStr}\n")
        wxError.write(content)
        wxError.close()

# fetch lat,long from google geocoding

config = frontmatter.load('./config/wx.md')
wxLocation = config['wx_config']['address']

session = requests.Session()
queryString = {'address': wxLocation,
    'key': key}
geocodeUrl = "https://maps.googleapis.com/maps/api/geocode/json"

response = session.get(geocodeUrl, params = queryString)

if response.status_code != 200 :
    appendError(f"Geocoding Failed with status code: {response.status_code}")
    print("Geocoding request failed. Exit.")
    sys.exit()

try :
    geocode = response.json()['results'][0]['geometry']['location']
except KeyError :
    appendError(f"Geocoding Failed with error: {response.json()}")
    print("Error parsing geocoding response. Exit.")
    sys.exit()

wxGeocode = f"{geocode['lat']},{geocode['lng']}"

session = requests.Session()
headers = {'user-agent': '(wx_scrape, mail@mattkjones.net)'}
session.headers.update(headers)

gridpointURL = f"https://api.weather.gov/points/{wxGeocode}"

response = getResponse(gridpointURL, session).json()['properties']

forecastURL = response['forecast']
forecastOffice = response['cwa']
forecastTimeZone = response['timeZone']
forecastLocationCity = response['relativeLocation']['properties']['city']
forecastLocationState = response['relativeLocation']['properties']['state']
forecastRelativeLocation = f"{forecastLocationCity}, {forecastLocationState}"

alertResponse = getResponse(f"https://api.weather.gov/alerts/active?area={forecastLocationState}", session).json()['features']
forecastResponse = getResponse(forecastURL, session).json()['properties']

forecastLocationElevation = int(forecastResponse['elevation']['value'] * 3.281)

# format json to markdown with timestamp
wxResult = open('./wx.md', 'w')
# city, state - elevation
# forecast office
# reported: date
heading = [f"## {forecastRelativeLocation}\n", 
    f"{forecastLocationElevation}ft\n", 
    f"{forecastOffice}\n", 
    f"*{datetime.datetime.now().astimezone(pytz.timezone(forecastTimeZone)).strftime('%b %d, %Y %H:%M')} {forecastTimeZone}*\n\n"]
wxResult.writelines(heading)

# Number of alerts
wxResult.write(f"*Active Alerts:* {len(alertResponse)}\n")

# Name - date
#   Temp unit / windspeed direction
#   detailed forecast
for period in forecastResponse['periods'] :
    report = [f"### {period['name']} - {datetime.datetime.fromisoformat(period['startTime']).strftime('%b %d, %Y')}\n",
        f"> #### **{period['temperature']}&deg;{period['temperatureUnit']}** / {period['windSpeed']} {period['windDirection']}\n",
        f"> {period['detailedForecast']}\n\n"]
    wxResult.writelines(report)

# alert descriptions
wxResult.write(f"## Active Alerts for {forecastLocationState}\n\n")

for alert in alertResponse :
    try :
        nwsHeadline = f"**{alert['properties']['parameters']['NWSheadline'][0]}**\n"
    except KeyError :
        nwsHeadline = "No NWS Headline\n"
    report = [nwsHeadline,
        f"*{alert['properties']['areaDesc']}*\n",
        f"{alert['properties']['headline']}\n",
        f"{alert['properties']['description']}\n",
        "---\n\n"]
    if forecastLocationCity in alert['properties']['areaDesc'] :
        markedReport = []
        for line in report :
            if line == "---\n\n" :
                continue
            line = "==" + line
            newLineIdx = line.find('\n')
            line = line[:newLineIdx] + '==' + line[newLineIdx:]
            markedReport.append(line)
        wxResult.writelines(markedReport)
    else :
        wxResult.writelines(report)

# save file to dashboard/wx.md
wxResult.close()
