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

from google.appengine.ext import db

import models

class JSError(webapp.RequestHandler):
    def get(self, keyword = False):
        message = self.request.get('message')
        url = self.request.get('url')
        line = self.request.get('line')
        logging.warning('JavaScript error: "%s" at %s on line %s' % (message, url, line))
        models.JSError(message=message, url=url, line=line, agent=self.request.headers['User-Agent']).put()

application = webapp.WSGIApplication(
        [('/jserror', JSError)]
        , debug=True)

def main():
    logging.getLogger().setLevel(logging.DEBUG)
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
