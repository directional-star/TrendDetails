#Copyright (c) 2012, www.directionalstar.com 

#See the file LICENSE.txt for copying permission.

from django.utils import simplejson as json
from google.appengine.ext import webapp
from google.appengine.api import users

import logging

class Handler(webapp.RequestHandler):
  def initialize(self, request, response):
    super(Handler, self).initialize(request, response)
    # Add a Django-like is_ajax() method to the request object
    request.is_ajax = lambda: \
      request.environ.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

  def doJson(self, data):
    user = users.get_current_user()
    data['loggedin'] = user.email() if user else False

    dump = json.dumps(data)
    logging.debug('outputting: %s' % (dump))

    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(dump)

  def checkUser(self):
    user = users.get_current_user()

    if not user:
      if self.request.is_ajax():
        self.doJson({'success':False,'error':'You have to log in to use this feature.','redirect':users.create_login_url(self.request.headers.get('Referer'))})
      else:
        self.redirect(users.create_login_url(self.request.uri))
      return False

    return user
