#Copyright (c) 2012, www.directionalstar.com 

#See the file LICENSE.txt for copying permission.

import os
import logging

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from google.appengine.api.urlfetch import fetch
from google.appengine.api import memcache
from google.appengine.api import users

from django.utils import simplejson as json

import config
import models
import handler

class EventHandler(handler.Handler):
  def get(self, target = False, action = False, label = '', value=False):
    user = self.checkUser()
    if not user:
      return

    if not target or not action:
      self.fail('Invalid event: no target/action specified')
      return

    evt = models.UserEvent(user=user, target=target, action=action, label=label)
    if not evt.put():
      self.fail('Event couldn\'t be recorded')
      return

    result = {'success': True}
    if users.is_current_user_admin():
      newbadges = models.checkForBadges(evt)
      if len(newbadges):
        result['badges'] = []
        for newbadge in newbadges:
          models.UserBadge(user=user, badge=newbadge.key()).put()
          result['badges'].append({
            'name': newbadge.name,
            'icon': newbadge.icon
          })

    self.doJson(result)

  def fail(self, error = False):
    self.doJson({
      'success': False,
      'error': error
    })


application = webapp.WSGIApplication(
    [(r'/event/(.*)/(.*)/(.*)/(.*)', EventHandler)
    ,(r'/event/(.*)/(.*)/(.*)', EventHandler)
    ,(r'/event/(.*)/(.*)', EventHandler)
    ,(r'/event/(.*)', EventHandler)
    ]
    , debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
