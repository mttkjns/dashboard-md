#!/usr/bin/env python3

#   this script hits yfinance api for real time market data and
#   formats the result into markdown for viewing

import requests
import frontmatter #https://github.com/eyeseast/python-frontmatter
import sys
import datetime
import pytz

# get api key from secrets, passed as an argument
try :
    key = sys.argv[1]
except IndexError :
    sys.exit("No api key provided. Exit.")

#get list of symbols from config
config = frontmatter.load('./config/ticker.md')
symbols = ','.join(config['ticker_config']['tickers'])

#hit api
session = requests.Session()
headers = {'X-API-KEY': key}
queryString = {"symbols": symbols}
session.headers.update(headers)
url = f"https://yfapi.net/v6/finance/quote?region=US&lang=en"

response = session.get(url, params = queryString)

if response.status_code != 200 :
    sys.exit(f"Bad status from https://yfapi.net/v6/finance/quote. Status Code: {response.status_code}")

# format json to markdown with timestamp
tickerResult = open('./tickers.md', 'w')

# time generated
tickerResult.write(f"# Tickers\n")
tickerResult.write(f"*{datetime.datetime.now(pytz.timezone('US/Eastern')).strftime('%b %d, %Y %H:%M')} EST*\n\n")


# Symbol - displayName
# regularMarketPrice, regularMarketChange, regularMarketChangePercent
# regularMarketDayRange, regularMarketVolume
# fiftyTwoWeekRange
for quote in response.json()['quoteResponse']['result'] :
    md = [f"#### {quote['symbol']} - {quote['shortName']}\n",
    f"{quote['regularMarketPrice']} | $ change: {quote['regularMarketChange']} | % change: {quote['regularMarketChangePercent']}\n",
    f"Day range: {quote['regularMarketDayRange']} 52 week range: {quote['fiftyTwoWeekRange']}\n",
    f"Vol: {quote['regularMarketVolume']} 3mo Avg Vol: {quote['averageDailyVolume3Month']}\n\n",
    "---\n\n"]
    tickerResult.writelines(md)

# save file to dashboard/ticker.md
tickerResult.close()
