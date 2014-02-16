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
import simplejson as json

from apiclient import discovery
from oauth2client import appengine
from oauth2client import client
from google.appengine.api import memcache, users
from google.appengine.ext import ndb

import webapp2
import jinja2
import string
import random

# from twilio.util import TwilioCapability
from twilio import twiml
from twilio.rest import TwilioRestClient
import twilio_auth



JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    autoescape=True,
    extensions=['jinja2.ext.autoescape'])

# CLIENT_SECRETS, name of a file containing the OAuth 2.0 information for this
# application, including client_id and client_secret, which are found
# on the API Access tab on the Google APIs
# Console <http://code.google.com/apis/console>
CLIENT_SECRETS = os.path.join(os.path.dirname(__file__), 'client_secrets.json')

#TWILIO
PARENT_ACCOUNT_SID = twilio_auth.get_parent_account_sid()
PARENT_AUTH_TOKEN = twilio_auth.get_parent_auth_token()

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
DEFAULT_USERSTORE_NAME = 'default_userstore'


def msgstore_key(msgstore_name=DEFAULT_MSGSTORE_NAME):
  return ndb.Key('Msgstore', msgstore_name)

def userstore_key(userstore_name=DEFAULT_USERSTORE_NAME):
  return ndb.Key('Userstore', userstore_name)

def get_current_uid():
  return users.get_current_user().user_id()

class Account(ndb.Model):
  user_id = ndb.StringProperty()
  text_conf = ndb.StringProperty()
  phone_no = ndb.StringProperty()
  twilio_sid = ndb.StringProperty()

class CalendarRecording(ndb.Model):
  user_id = ndb.StringProperty()
  calendar_id = ndb.StringProperty(indexed=False)
  #recording = file property?

############## HANDLERS ####################################

class PhoneInput(webapp2.RequestHandler):
  def get(self):
    template = JINJA_ENVIRONMENT.get_template('phone_input.html')
    self.response.write(template.render())

  def post(self):
    # create a user entry
    userstore_name = self.request.get('userstore_name',
                                  DEFAULT_USERSTORE_NAME)
    account = Account(parent = userstore_key(userstore_name))
    account.user_id = get_current_uid()
    print get_current_uid()
    # text the confirmation code
    # client = TwilioRestClient(PARENT_ACCOUNT_SID, PARENT_AUTH_TOKEN)
    phone_no = self.request.get('phone_no')
    code=string.ascii_lowercase+string.digits
    verification_code=''.join(random.choice(code) for i in range(8))
    message="What's up? Enter %s on the sign up page to verify your Can't Pickup account! Thanks :)"%(verification_code)   
    # message = client.messages.create(to=phone_no, from_="+15402239053",
                                         # body=message)
    
    # store the user_id and text conf code
    account.phone_no = phone_no
    account.text_conf = verification_code
    account.put()

class ConfirmCode(webapp2.RequestHandler):
  def post(self):
    conf_input = self.request.get('conf')
    print "conf: ", conf_input
    account = Account.query(Account.user_id==get_current_uid()).get()
    if account:
      print account.text_conf, conf_input
    if account and account.text_conf == conf_input:
      # success
      # create twilio account
      client = TwilioRestClient(PARENT_ACCOUNT_SID, PARENT_AUTH_TOKEN)
      subaccount = client.accounts.create()
      account.twilio_sid = subaccount.sid
      account.put()
      # pass
      # redirect to next step: add recording handler?
    else:
      response = {'error':'wrong code'}
      JSON = json.dumps(response)
      self.response.headers.add_header('content-type', 'application/json', charset='utf-8')
      self.response.out.write(JSON)

class AddRecordingHandler(webapp2.RequestHandler):
  @decorator.oauth_aware
  def get(self):
    variables = {
      'url': decorator.authorize_url(),
      'has_credentials': decorator.has_credentials(),
    }
    if decorator.has_credentials():
      http = decorator.http()
      result = service.calendarList().list().execute(http=http)
      cals = result.get('items', [])
      variables['calendar_list'] = cals

    template = JINJA_ENVIRONMENT.get_template('main.html')
    self.response.write(template.render(variables))

  def post(self):
    msgstore_name = self.request.get('msgstore_name',
                                    DEFAULT_MSGSTORE_NAME)
    cal_recording = CalendarRecording(parent = msgstore_key(msgstore_name))
    if users.get_current_user():
      cal_recording.user_id = users.get_current_user().user_id()

    cal_recording.calendar_id = self.request.get('calendar_id')
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
     ('/', PhoneInput),
     ('/confirm_code', ConfirmCode),
     ('/create', AddRecordingHandler),
     ('/success', SuccessHandler),
     ('/call', CallHandler),
     (decorator.callback_path, decorator.callback_handler()),
    ],
    debug=True)
