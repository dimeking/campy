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
# [START imports]
import logging
import os
import json

import flask
from flask import request, render_template

from datetime import datetime, timedelta, date
from urlparse import parse_qs, urlparse

import campy_models as models

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

SITE_URL = 'https://www.recreation.gov'
CODE_PARAM = 'contractCode=NRSO'

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


def getCalendarURL(id, date):
    ACTION_URL = '/campsiteCalendar.do?'
    VIEW_PARAMS = 'page=calendar' + '&' + CODE_PARAM

    url = SITE_URL + ACTION_URL + VIEW_PARAMS
    url = url + '&parkId=' + id
    url = url + '&calarvdate=' + date

    return url

def getPropertyURL(id):
    ACTION_URL = '/campgroundDetails.do?'
    VIEW_PARAMS = CODE_PARAM

    url = SITE_URL + ACTION_URL + VIEW_PARAMS
    url = url + '&parkId=' + id

    return url

TOP_PROPERTIES = [
    {'id':'72393', 'name':'Point Reyes NSS', 'url':getPropertyURL('72393')}, 
    {'id':'70926', 'name':'TUOLUMNE MEADOWS, Yosemite NP', 'url':getPropertyURL('70926')}, 
    {'id':'70925', 'name':'UPPER PINES, Yosemite NP', 'url':getPropertyURL('70925')}, 
    {'id':'70928', 'name':'LOWER PINES, Yosemite NP', 'url':getPropertyURL('70928')}, 
    {'id':'70927', 'name':'NORTH PINES, Yosemite NP', 'url':getPropertyURL('70927')}, 
    {'id':'71531', 'name':'FALLEN LEAF, Lake Tahoe', 'url':getPropertyURL('71531')}, 
    {'id':'70980', 'name':'Scorpion, Channel Islands NP', 'url':getPropertyURL('70980')},
    {'id':'73984', 'name':'Pinnacles NP', 'url':getPropertyURL('73984')}, 
     ]

def search_property_name(response_text):

    name_str = "<span id='cgroundName'"
    idx = response_text.find(name_str, 0)
    if idx < 0:
        return
    idx = response_text.find('>', idx)

    edx = response_text.find('</span>', idx)
    name = response_text[idx+1:edx-1]
    return name
    

def search_available_dates(response_text):
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
    day = 'Sat' if day not in daysofweek else day
    return daysofweek[day], day

def get_property_details(tracker_url):
    params = parse_qs(urlparse(tracker_url).query)
    if 'parkId' not in params:
        return
    id = params['parkId'][0]

    # [START requests_get]
    url = getPropertyURL(id)
    response = requests.get(url)
    response.raise_for_status()
    # [END requests_get]

    name = search_property_name(response.text)    

    return { 'id': id, 'name': name, 'url': tracker_url }

def generate_tracked_info(properties, day):

    # search for saturdays for 6 months
    dow, day = dayofweek(day)
    search_dates = getSearchDates(dow, 26)

    # search in all properties
    tracked_info = properties
    # tracked_info['timestamp'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # tracked_info['dayofweek'] = dayofweek(day)
    for prop in properties:
        prop['available_dates'] = {} if 'available_dates' not in prop else prop['available_dates']
        prop['available_dates'][day] = []
        # prop['search dates'] = search_dates
        print "property name: ", prop['name']
        
        for search_date in search_dates:
            # print "search date: ", search_date

            url = getCalendarURL(prop['id'], search_date)
    
            # [START requests_get]
            response = requests.get(url)
            response.raise_for_status()
            # [END requests_get]

            available_dates = search_available_dates(response.text)
            if not any(available_dates):
                continue

            if search_date in available_dates:
                # print "Eureka: ", search_date
                prop['available_dates'][day].append({'date': search_date, 'url': url})
                # send_approved_mail('{}@appspot.gserviceaccount.com'.format(
                #     app_identity.get_application_id()), prop['name'], url, search_date)


    return tracked_info

@app.route('/')
def index():

    day = request.args.get('dayofweek') if 'dayofweek' in request.args else None
    days = request.args.get('days') if 'days' in request.args else None
    useremail = request.args.get('useremail') if 'useremail' in request.args else None
    
    tracked_info = generate_tracked_info(TOP_PROPERTIES, 'Fri')
    tracked_info = generate_tracked_info(tracked_info, 'Sat')

    # [START render_template]
    return render_template(
        'submitted_form.html',
        username='Every One',
        properties=tracked_info)
    # [END render_template]

# [START form]
@app.route('/form')
def form():
    return render_template('form.html')
# [END form]


# [START submitted]
@app.route('/submitted', methods=['POST'])
def submitted_form():
    username = request.form['name']
    email = request.form['email']
    tracker_url = request.form['tracker_url']
    frequency = request.form['frequency']
    alerts = request.form['alerts']

    models.store_user_info(email, {"name" : username}, {"frequency": frequency, "alerts": alerts})
    property_details = get_property_details(tracker_url)
    models.store_tracker_item(email, property_details)

    trackers = models.get_tracker_list(email) 
    properties = trackers if any(trackers) else TOP_PROPERTIES   
    print "properties or trackers: ", properties    
    tracked_info = generate_tracked_info(properties, 'Fri')
    tracked_info = generate_tracked_info(tracked_info, 'Sat')
    # models.store_tracked_info(email, tracked_info)

    # [END submitted]
    # [START render_template]
    return render_template(
        'submitted_form.html',
        username=username,
        properties=tracked_info)
    # [END render_template]

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500
# [END app]
