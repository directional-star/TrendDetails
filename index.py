#Copyright (c) 2012, www.directionalstar.com 

#See the file LICENSE.txt for copying permission.

import os
import re
import datetime
import logging
import urllib

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template
from google.appengine.ext import db
from google.appengine.api import users

import models
import api

class MainPage(webapp.RequestHandler):
  def get(self, keyword = False):
    self.response.headers['Content-Type'] = 'text/html'

    day = None
    debug = False
    todate = datetime.date.today()

    if not keyword:
      keyword = ''

    elif keyword[:3] == 'day':
      keyword = ''
      day = keyword[4:]
      m = re.match('(\d{4})-(\d{2})-(\d{2})', day)
      if m:
        date = datetime.date(m.group(1), m.group(2), m.group(3))
      else:
        day = None

    elif keyword == '_dbg':
      debug = True
      keyword = False

    if not day:
      day = todate.isoformat()
      date = todate

    keywordsModel = models.summarizeDailyTrends(date)
    if keywordsModel:
      keywords = keywordsModel.get('keywords')
    else:
      keywords = False

    if self.request.get('_escaped_fragment_'):
      keyword = self.request.get('_escaped_fragment_')
      keyword = urllib.unquote(keyword)

    firstDay = models.DailyTrends.all().order('date').get()
    if firstDay:
      minDate = (firstDay.date - datetime.date.today()).days
    else:
      minDate = 0

    articles = False
    if len(keyword):
      apis = api.ApiHandler(self.request.remote_addr, parse=True)
      kw_q = urllib.quote(keyword)
      articles = {
        'bing':  apis.requestBing(kw_q),
        'news':  apis.requestNews(kw_q),
        'blogs': apis.requestBlogs(kw_q),
        'wiki':  apis.requestWiki(kw_q)
      }

    user = users.get_current_user()
    if user:
      userData = {
        'email':    user.email,
        'settings': models.getUserSettings(user)
      }

    else:
      userData = False

    templateVars = {
      'keyword':  keyword,
      'keywords': keywords,
      'articles': articles,
      'day':      day,
      'today':    todate.isoformat(),
      'minDate':  minDate,

      'userData': userData,
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

    if debug:
      self.response.out.write(templateVars)
      for dt in models.DailyTrends.all().order('date'):
        self.response.out.write(dt.date)
      return

    path = os.path.join(os.path.dirname(__file__), 'tpl', 'index.html')
    self.response.out.write(template.render(path, templateVars))

application = webapp.WSGIApplication(
    [('/', MainPage),
     (r'/(.*)', MainPage)]
    , debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
