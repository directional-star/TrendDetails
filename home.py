#Copyright (c) 2012, www.directionalstar.com 

#See the file LICENSE.txt for copying permission.

import os
import re
import datetime
import logging

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.api import users

from google.appengine.ext import db

import models
import handler

class UserLogout(handler.Handler):
  def get(self):
    user = self.checkUser()
    if user:
      self.redirect(users.create_logout_url(self.request.headers.get('Referer')))
      return

class UserHome(handler.Handler):
  def get(self):
    user = self.checkUser()
    if not user:
      return

    settings = models.getUserSettings(user)

    templateVars = {
      'settings': settings.list(),
      'admin': users.is_current_user_admin(),
    }

    self.response.headers['Content-Type'] = 'text/html'
    path = os.path.join(os.path.dirname(__file__), 'tpl', 'home.html')
    self.response.out.write(template.render(path, templateVars))

class UserSet(handler.Handler):

  def post(self):
    user = self.checkUser()
    if not user:
      return

    name = self.request.get('name')
    value = self.request.get('value')
    if not name or not value:
      self.doJson({'success':False,'error':'Missing data'})
      return

    settings = models.getUserSettings(user)
    success = settings.set(name, value)
    settings.put()

    self.doJson({'success':success})
    
class UserBadges(handler.Handler):
  def get(self):
    user = self.checkUser()
    if not user:
      return

    settings = models.getUserSettings(user)

    # User badges
    ownBadges = []
    badges = models.UserBadge.all().order('date')
    for badge in badges:
      props = {
        'name': badge.badge.name,
        'desc': badge.badge.desc,
        'icon': badge.badge.icon if badge.badge.icon else 'newbie'
      }
      ownBadges.append({'badge':props,'date':badge.date})

    templateVars = {
      'badges': ownBadges,
      'admin': users.is_current_user_admin(),
    }

    if users.is_current_user_admin():
      allBadges = []
      badges = models.BadgeDef.all().order('target').order('action').order('after')
      for badge in badges:
        props = {
          'name': badge.name,
          'desc': badge.desc,
          'icon': badge.icon if badge.icon else 'newbie',
          'target': badge.target,
          'action': badge.action
        }
        allBadges.append({'badge':props,'edit':True,'key':badge.key()})

      templateVars['allbadges'] = allBadges
      
    self.response.headers['Content-Type'] = 'text/html'
    path = os.path.join(os.path.dirname(__file__), 'tpl', 'badges.html')
    self.response.out.write(template.render(path, templateVars))

  def post(self):
    if users.is_current_user_admin():
      delkey = self.request.get('delete')
      if delkey:
        models.BadgeDef.get(delkey).delete()
      else:
        badge = models.BadgeDef()
        badge.name = self.request.get('name')
        badge.desc = self.request.get('desc')
        badge.target = self.request.get('target')
        badge.action = self.request.get('action')
        badge.after = int(self.request.get('after'))
        badge.icon = self.request.get('icon')
        badge.put()

    self.redirect('/badges')

application = webapp.WSGIApplication(
    [('/home', UserHome)
    ,('/home/set', UserSet)
    ,('/badges', UserBadges)
    ,('/logout', UserLogout)]
    , debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
