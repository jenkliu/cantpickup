#!/usr/bin/env python
#
# Copyright 2013 Google Inc.
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
#
"""Starting template for Google App Engine applications.

Use this project as a starting point if you are just beginning to build a Google
App Engine project. Remember to download the OAuth 2.0 client secrets which can
be obtained from the Developer Console <https://code.google.com/apis/console/>
and save them as 'client_secrets.json' in the project directory.
"""

import httplib2
import logging
import os
import datetime as dt

from apiclient import discovery
from oauth2client import appengine
from oauth2client import client
from google.appengine.api import memcache, users
from google.appengine.ext import ndb

import webapp2
import jinja2

# from twilio.util import TwilioCapability
from twilio import twiml


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    autoescape=True,
    extensions=['jinja2.ext.autoescape'])

# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

# Helpful message to display in the browser if the CLIENT_SECRETS file
# is missing.
MISSING_CLIENT_SECRETS_MESSAGE = """
<h1>Warning: Please configure OAuth 2.0</h1>
<p>
To make this sample run you will need to populate the client_secrets.json file
found at:
</p>
<p>
<code>%s</code>.
</p>
<p>with information found on the <a
href="https://code.google.com/apis/console">APIs Console</a>.
</p>
""" % CLIENT_SECRETS

http = httplib2.Http(memcache)
service = discovery.build('calendar', 'v3', http=http)
decorator = appengine.oauth2decorator_from_clientsecrets(
    CLIENT_SECRETS,
    scope=[
      'https://www.googleapis.com/auth/calendar',
      'https://www.googleapis.com/auth/calendar.readonly',
    ],
    message=MISSING_CLIENT_SECRETS_MESSAGE)


DEFAULT_MSGSTORE_NAME = 'default_msgstore'

def msgstore_key(msgstore_name=DEFAULT_MSGSTORE_NAME):
  return ndb.Key('Msgstore', msgstore_name)

class Account(ndb.Model):
  user = ndb.UserProperty()
  phone_no = ndb.StringProperty()
  # twilio_id

class CalendarRecording(ndb.Model):
  user = ndb.UserProperty()
  calendar_id = ndb.StringProperty(indexed=False)
  #recording = file property?

class MainHandler(webapp2.RequestHandler):

  @decorator.oauth_aware
  def get(self):
    variables = {
      'url': decorator.authorize_url(),
      'has_credentials': decorator.has_credentials(),
    }
    if decorator.has_credentials():
      print "has credentials"

      http = decorator.http()
      result = service.calendarList().list().execute(http=http)
      cals = result.get('items', [])
      variables['calendar_list'] = cals
    # # for cal in cals:
    # #   print cal['summary']


    template = JINJA_ENVIRONMENT.get_template('main.html')
    self.response.write(template.render(variables))

class AddRecordingHandler(webapp2.RequestHandler):
  def post(self):
    msgstore_name = self.request.get('msgstore_name',
                                    DEFAULT_MSGSTORE_NAME)
    cal_recording = CalendarRecording(parent = msgstore_key(msgstore_name))
    if users.get_current_user():
      cal_recording.user = users.get_current_user()

    cal_recording.calendar_id = self.request.get('calendar_id')

    ## TWILIO STUFF     
    # account_sid = "ACXXXXXXXXXXXXXXX"
    # auth_token = "secret"
     
    # capability = TwilioCapability(account_sid, auth_token)
    # capability.allow_client_incoming("tommy")
    # print capability.generate()

    #####################

    cal_recording.put()

    self.redirect('/success')

class SuccessHandler(webapp2.RequestHandler):
    def get(self):
      template = JINJA_ENVIRONMENT.get_template('success.html')
      self.response.write(template.render())

class CallHandler(webapp2.RequestHandler):
  def post(self):
    resp = twiml.Response()
    resp.say("Hello Monkey")
   
    self.response.headers['Content-Type'] = 'text/xml' 
    self.response.write(str(resp))

  # param: phone number
  # get the user associated with the phone number
  # get the callrecordings associated with this user
  # get the calendar_id associated with the callrecordings
  # cal_id = 

  # get the current time
  # tNow  = dt.datetime.now()
  # tHrBefore = tNow - dt.timedelta(minutes = tNow.minute, seconds = tNow.second, microseconds =  tNow.microsecond)
  # tHrAfter = tHrBefore + dt.timedelta(hours = 1)
  # result = service.events().list(calendarId = cal_id, timeMin = tHrBefore.isoformat(), timeMax = tHrAfter.isoformat()).execute(http=http)
  # events = result.get('items', [])
  # if len(events) > 0:
  #   # busy!!!
  # else:
  #   # redirect to phone number

app = webapp2.WSGIApplication(
    [
     ('/', MainHandler),
     ('/add', AddRecordingHandler),
     ('/success', SuccessHandler),
     ('/call', CallHandler),
     (decorator.callback_path, decorator.callback_handler()),
    ],
    debug=True)
