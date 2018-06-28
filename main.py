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

REC_SITE_URL = 'https://www.recreation.gov'
RA_SITE_URL = 'https://www.reserveamerica.com'
CODE_PARAM = 'contractCode='

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

def getSiteURL(id):
    return REC_SITE_URL if int(id)<100000 else RA_SITE_URL

def getCodeParam(id):
    code = {0: 'NRSO', 1: 'EB', 10: 'PRCG'}
    idx = int(id)/100000
    return CODE_PARAM+code[idx]

def getCalendarURL(id, date):
    ACTION_URL = '/campsiteCalendar.do?'
    VIEW_PARAMS = 'page=calendar' + '&' + getCodeParam(id)

    url = getSiteURL(id) + ACTION_URL + VIEW_PARAMS
    url = url + '&parkId=' + id
    url = url + '&calarvdate=' + date

    return url

def getPropertyURL(id):
    ACTION_URL = '/campgroundDetails.do?'
    VIEW_PARAMS = getCodeParam(id)

    url = getSiteURL(id) + ACTION_URL + VIEW_PARAMS
    url = url + '&parkId=' + id

    return url

TOP_PROPERTIES = [
    {'id':'72393', 'name':'Point Reyes National Seashore Campground, CA', 'url':getPropertyURL('72393')}, 
    {'id':'70926', 'name':'TUOLUMNE MEADOWS, CA', 'url':getPropertyURL('70926')}, 
    {'id':'70925', 'name':'UPPER PINES, CA', 'url':getPropertyURL('70925')}, 
    {'id':'70928', 'name':'LOWER PINES, CA', 'url':getPropertyURL('70928')}, 
    {'id':'70927', 'name':'NORTH PINES, CA', 'url':getPropertyURL('70927')}, 
    {'id':'71531', 'name':'FALLEN LEAF CAMPGROUND, CA', 'url':getPropertyURL('71531')}, 
    {'id':'70980', 'name':'SANTA CRUZ SCORPION, CA', 'url':getPropertyURL('70980')},
    {'id':'73984', 'name':'PINNACLES CAMPGROUND, CA', 'url':getPropertyURL('73984')}, 
    {'id':'110457', 'name':'Point Pinole Regional Shoreline, CA', 'url':getPropertyURL('110457')}, 
    {'id':'110453', 'name':'Coyote Hills Regional Park, CA', 'url':getPropertyURL('110453')}, 
    {'id':'110003', 'name':'Del Valle, CA', 'url':getPropertyURL('110003')}, 
    {'id':'110028', 'name':'Sunol, CA', 'url':getPropertyURL('110028')}, 
    {'id':'110452', 'name':'Black Diamond Mines Regional Preserve, CA', 'url':getPropertyURL('110452')}, 
    {'id':'1060800', 'name':'Clear Lake Campground, CA', 'url':getPropertyURL('1060800')}, 
    {'id':'1061750', 'name':'CAMPGROUND BY THE LAKE, CA', 'url':getPropertyURL('1061750')}, 
     ]
def top_property_list():
    return [prop['id'] for prop in TOP_PROPERTIES]

def search_property_name(response_text):

    name_str = "<span id='cgroundName'"
    idx = response_text.find(name_str, 0)
    if idx < 0:
        return
    idx = response_text.find('>', idx)

    edx = response_text.find('</span>', idx)
    name = response_text[idx+1:edx]
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

def generate_available_dates(property_id, day):

    # search for saturdays for 6 months
    dow, day = dayofweek(day)
    search_dates = getSearchDates(dow, 26)

    # search in all properties
    timestamp = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    property_available_dates = {}
    property_available_dates[day] = {'timestamp':timestamp, 'dates':[]}
    
    for search_date in search_dates:
        # print "search date: ", search_date

        url = getCalendarURL(property_id, search_date)

        # [START requests_get]
        response = requests.get(url)
        response.raise_for_status()
        # [END requests_get]

        available_dates = search_available_dates(response.text)
        if not any(available_dates):
            continue

        if search_date in available_dates:
            # print "Eureka: ", search_date
            property_available_dates[day]['dates'].append({'date': search_date, 'url': url})
            # send_approved_mail('{}@appspot.gserviceaccount.com'.format(
            #     app_identity.get_application_id()), prop['name'], url, search_date)


    return property_available_dates

def get_date(date_str):
    m, d, y = date_str.split('/')
    dt = date(int(y),int(m),int(d))
    return dt

# def resolve_tracked_info(tracked_info):
#     fri_dates = [get_date(dt['date']).toordinal() for dt in tracked_info['available_dates']['Fri']]
#     sat_dates = [get_date(dt['date']).toordinal() for dt in tracked_info['available_dates']['Sat']]

#     # pick Fridays where Sat is available
#     f_dates = [date.fromordinal(dt).strftime('%m/%d/%Y') for dt in fri_dates if dt+1 in sat_dates]
#     fr_dates = [dt for dt in tracked_info['available_dates']['Fri'] if dt['date'] not in f_dates]
#     tracked_info['available_dates']['Fri'] = fr_dates

#     return tracked_info

def get_availability(useremail=None):
    # get all properties of user or top properties 
    property_list = models.get_user_properties(useremail) if useremail else models.get_properties()
    property_ids = property_list if any(property_list) else top_property_list()   
    print "property_ids: ", property_ids    
    
    # show its availability
    properties = []
    for proprety_id in property_ids:
        prop = models.get_property_details(proprety_id)
        prop['available_dates'] = models.get_property_available_dates(proprety_id)
        if not prop['available_dates']:
            prop['available_dates'] = {}
        if 'Fri' not in prop['available_dates'] or not prop['available_dates']['Fri']:
            prop['available_dates']['Fri'] = {'timestamp':'', 'dates':[]}
        if 'Sat' not in prop['available_dates'] or not prop['available_dates']['Sat']:
            prop['available_dates']['Sat'] = {'timestamp':'', 'dates':[]}

        properties.append(prop)

    return properties

def update_property_availability(prop_id):
    # save this property availability
    fri_available_dates = generate_available_dates(prop_id, 'Fri')
    models.save_property_dates(prop_id, fri_available_dates)
    sat_available_dates = generate_available_dates(prop_id, 'Sat')
    models.save_property_dates(prop_id, sat_available_dates)

    prop = models.get_property_details(prop_id)
    prop['available_dates'] = models.get_property_available_dates(prop_id)
    return prop

def update_availability(useremail=None):
    # get all properties of user or top properties 
    property_list = models.get_user_properties(email) if useremail else models.get_properties()
    property_ids = property_list if any(property_list) else top_property_list()   
    print "property_ids: ", property_ids    

    properties = []
    for property_id in property_ids:
        prop = update_property_availability(property_id)
        properties.append(prop)

    return properties

@app.route('/start')
def start():
    print "start: "
    show = request.args.get('show') if 'show' in request.args else None

    for property_details in TOP_PROPERTIES:
        models.save_property_details(property_details['id'], property_details)

    properties = update_availability()
    return flask.jsonify(properties=properties)


@app.route('/refresh')
def refresh():
    print "refresh: "
    useremail = request.args.get('useremail') if 'useremail' in request.args else None
    show = request.args.get('show') if 'show' in request.args else None

    # refresh availability 
    # get all properties of user or top properties
    properties = update_availability(useremail)

    return flask.jsonify(properties=properties)

@app.route('/')
def index():

    # day = request.args.get('dayofweek') if 'dayofweek' in request.args else None
    # days = request.args.get('days') if 'days' in request.args else None
    useremail = request.args.get('useremail') if 'useremail' in request.args else None
    
    # refresh availability if need be
    # get all properties of user or top properties and show its availability
    properties = get_availability(useremail)

    # [START render_template]
    return render_template(
        'submitted_form.html',
        username='Every One',
        properties=properties)
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

    # save this property details
    models.save_user_info(email, {"name" : username}, {"frequency": frequency, "alerts": alerts})
    property_details = get_property_details(tracker_url)
    models.save_property_details(property_details['id'], property_details)
    models.save_user_property(email, property_details['id'])

    # refresh this property availability
    update_property_availability(property_details['id'])

     # get all properties of user or top properties and show its availability
    properties = get_availability(email)   

    # [END submitted]
    # [START render_template]
    return render_template(
        'submitted_form.html',
        username=username,
        properties=properties)
    # [END render_template]

@app.errorhandler(500)
def server_error(e):
    logging.exception('An error occurred during a request.')
    return """
    An internal error occurred: <pre>{}</pre>
    See logs for full stacktrace.
    """.format(e), 500
# [END app]
