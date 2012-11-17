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
from django.utils import simplejson as json

import models
import handler

class FavPage(handler.Handler):
  def get(self, keyword = False):
    user = self.checkUser()
    if not user:
      return

    keywordsModel = models.getFavorites(user)
    if keywordsModel:
      keywords = keywordsModel.keywords
    else:
      keywords = False

    if self.request.is_ajax():
      self.doJson({'success':True,'keywords':keywords})
      return

    firstDay = models.DailyTrends.all().order('date').get()
    if firstDay:
      minDate = (firstDay.date - datetime.date.today()).days
    else:
      minDate = 0

    templateVars = {
      'keywords': keywords,
      'minDate': minDate,

      'userData': {
        'email':    user.email,
        'settings': models.getUserSettings(user)
      },
      'admin': users.is_current_user_admin(),

      # javascript templates
      'result':   {
        'title':  '{title}',
        'info':   '{info}',
        'text':   '{text}',
        'link':   '{link}'
      },
      'hotkeyword': '{hotKeyword}'
    }

    self.response.headers['Content-Type'] = 'text/html'
    path = os.path.join(os.path.dirname(__file__), 'tpl', 'favorites.html')
    self.response.out.write(template.render(path, templateVars))

  def post(self):
    if not self.request.is_ajax():
      return

    user = self.checkUser()
    if not user:
      return

    keyword = self.request.get('keyword')
    if not keyword:
      self.doJson({'success':False,'error':'Missing keyword'})
      return

    keywordsModel = models.getFavorites(user)
    if not keywordsModel:
      keywordsModel = models.FavoriteKeywords(user = user, keywords = [])

    keywords = keywordsModel.keywords
    if keyword in keywords:
      message = '<i>%s</i> was removed from <a href="/favorites">your favorite keywords</a>' % (keyword)
      keywords.remove(keyword)
    else:
      message = '<i>%s</i> was added to <a href="/favorites">your favorite keywords</a>' % (keyword)
      keywords.append(keyword)
      keywords.sort()

    keywordsModel.keywords = keywords
    keywordsModel.put()

    self.doJson({'success':True,'keywords':keywords,'message':message})


application = webapp.WSGIApplication(
    [('/favorites', FavPage),
     (r'/favorites/(.*)', FavPage)]
    , debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
