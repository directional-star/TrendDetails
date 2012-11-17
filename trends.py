#Copyright (c) 2012, www.directionalstar.com 

#See the file LICENSE.txt for copying permission.

import os
import re
import time
import datetime
import logging

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from google.appengine.api.urlfetch import fetch
from django.utils import simplejson as json

from google.appengine.ext import db
from google.appengine.api import memcache

import models

class FetchTrends(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        xml = fetch('http://www.google.com/trends/hottrends/atom/hourly')
        if not xml:
            loggging.error('couldn\'t fetch trends')
            self.out({'success':False, 'error':'fetch error'})
            return

        keywords = re.findall('<a href="[^"]*">(.*)</a>', xml.content)
        logging.debug('fetched keywords: %s' % (", ".join(keywords)))

        dbRow = models.HotKeywords(keywords = keywords)
        dbRow.put()

        self.out({'success': True, 'keywords': keywords})

    def out(self, ret):
        dump = json.dumps(ret)
        logging.debug('outputting: %s' % (dump))
        self.response.out.write(dump)

class FetchedLast(webapp.RequestHandler):
    def get(self):
        self.response.headers['Content-Type'] = 'application/json'

        lastRow = models.HotKeywords.all().order('-date').get()
        last = lastRow.date
        nextt = last+datetime.timedelta(seconds=3660) # 60*60 + a minute just to make sure
        timeformat = '%Y-%m-%dT%H:%M:%SZ'
        # last = datetime.datetime.now()
        # nextt = last+datetime.timedelta(seconds=163)
        self.response.out.write(json.dumps({
            'success': bool(lastRow),
            'last': last.strftime(timeformat),
            'next': nextt.strftime(timeformat)
        }))

class DailyTrends(webapp.RequestHandler):
    def get(self, date = False):
        self.response.headers['Content-Type'] = 'application/json'

        today = datetime.date.today()

        if date:
            date = datetime.date.fromtimestamp(time.mktime(time.strptime(date, '%Y-%m-%d')))
        else:
            date = datetime.date.fromtimestamp(time.time() - 3600)

        ordering = self.request.get('o')

        self.out(models.summarizeDailyTrends(date, ordering))

    def out(self, ret):
        dump = json.dumps(ret)
        logging.debug('outputting: %s' % (dump))
        self.response.out.write(dump)

class Sitemap(webapp.RequestHandler):
  def get(self):
    date = datetime.date.today()
    topics = models.summarizeDailyTrends(date,'popular')

    self.response.headers['Content-Type'] = 'text/xml' 
    path = os.path.join(os.path.dirname(__file__), 'tpl', 'sitemap.xml')
    self.response.out.write(template.render(path, {'topics':topics}))

application = webapp.WSGIApplication(
        [('/trends/fetch',          FetchTrends)
        ,('/trends/last',           FetchedLast)
        ,('/trends/daily',          DailyTrends)
        ,(r'/trends/daily/(.*)',    DailyTrends)
        ,('/sitemap.xml', Sitemap)
        ]
        , debug=True)

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
