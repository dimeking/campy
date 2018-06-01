# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [START app]
import logging
import os
import json

import flask
from flask import request

# [START imports]
from datetime import datetime, timedelta, date

from google.appengine.api import app_identity
from google.appengine.api import mail

import requests
import requests_toolbelt.adapters.appengine

# Use the App Engine Requests adapter. This makes sure that Requests uses
# URLFetch.
if 'MONKEY_PATCH' in os.environ:
    requests_toolbelt.adapters.appengine.monkeypatch()
# [END imports]

app = flask.Flask(__name__)

PARKS = [
    {'id':'72393', 'name':'Point Reyes NSS'}, 
    {'id':'70926', 'name':'TUOLUMNE MEADOWS, Yosemite NP'}, 
    {'id':'70925', 'name':'UPPER PINES, Yosemite NP'}, 
    {'id':'70928', 'name':'LOWER PINES, Yosemite NP'}, 
    {'id':'70927', 'name':'NORTH PINES, Yosemite NP'}, 
    {'id':'71531', 'name':'FALLEN LEAF, Lake Tahoe'}, 
    {'id':'70980', 'name':'Scorpion, Santa Cruz Island, Channel Islands NP'},
    {'id':'73984', 'name':'Pinnacles NP'}, 
     ]
SITE_URL = 'https://www.recreation.gov'
CODE_PARAM = '&contractCode=NRSO'

def getNextDate(dayofweek):
    # next fri/sat while (Mon-Sun: 0-6)
    today = date.today()
    that_day = today + timedelta( (dayofweek-today.weekday()) % 7 )
    return that_day

def getSearchDates(dayofweek, weeks):
    search_dates = []
    next_date = None

    for i in range(weeks):
        next_date = (next_date + timedelta(7)) if next_date else getNextDate(dayofweek)
        search_dates.append(next_date.strftime('%m/%d/%Y'))
        
    return search_dates


def getCalendarURL(parkid, date):
    ACTION_URL = '/campsiteCalendar.do?'
    VIEW_PARAMS = 'page=calendar' + CODE_PARAM

    url = SITE_URL + ACTION_URL + VIEW_PARAMS
    url = url + '&parkId=' + parkid
    url = url + '&calarvdate=' + date

    return url

def search(response_text):
    available_dates = []
    idx = 0
    while True:
        av_str = "<td class='status a"
        # av_sat_str = "<td class='status a sat' >"
        # av_sun_str = "<td class='status a sun' >"
        idx = response_text.find(av_str, idx)
        if idx < 0:
            break
        idx = idx + len(av_str)

        dt_str = "arvdate="
        idx = response_text.find(dt_str, idx)
        if idx < 0:
            continue
        idx = idx + len(dt_str)
        
        e_dt_str = "&"
        e_idx = response_text.find(e_dt_str, idx)
        if e_idx < 0:
            continue
        e_idx = e_idx + len(e_dt_str) - 1

        date_str = response_text[idx:e_idx]
        m, d, y = date_str.split('/')
        dt = date(int(y),int(m),int(d)).strftime('%m/%d/%Y')
        # print "available date: ", dt
        available_dates.append(dt)

    return available_dates

def send_approved_mail(sender_address, name, url, search_date):
    print "goto url: ", url

    # [START send_mail]
    mail.send_mail(sender=sender_address,
                   to="Hari Raja <raja_hh@hotmail.com>",
                   subject="Checkout campgrounds at {} on {}.".format(name, search_date),
                   body="""Hari Raja,

Checkout {} campgrounds at {} on {}.

Please let us know if you have any questions.

The Campy Team
""".format(name, url, search_date))
    # [END send_mail]

def dayofweek(day):
    daysofweek = {'Mon': 0, 'Tue': 1, 'Wed': 2, 'Thu': 3, 'Fri': 4, 'Sat': 5, 'Sun': 6}
    return daysofweek[day] if day in daysofweek else 5 # Sat

@app.route('/')
def index():

    day = request.args.get('dayofweek') if 'dayofweek' in request.args else None
    days = request.args.get('days') if 'days' in request.args else None
    
    parks = PARKS
    # search for saturdays for 6 months
    search_dates = getSearchDates(dayofweek(day), 26)

    # search in all parks
    for park in parks:
        park['available dates'] = []
        # park['search dates'] = search_dates
        print "park name: ", park['name']
        
        for search_date in search_dates:
            # print "search date: ", search_date

            url = getCalendarURL(park['id'], search_date)
    
            # [START requests_get]
            response = requests.get(url)
            response.raise_for_status()
            # [END requests_get]

            available_dates = search(response.text)
            if not any(available_dates):
                continue

            if search_date in available_dates:
                print "Eureka: ", search_date
                park["available dates"].append({'date': search_date, 'url': url})
                # send_approved_mail('{}@appspot.gserviceaccount.com'.format(
                #     app_identity.get_application_id()), park['name'], url, search_date)


    return flask.jsonify(parks)


@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500
# [END app]
