import os
import re
import logging
import urllib

from google.appengine.dist import use_library
use_library('django', '1.2')

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from google.appengine.api.urlfetch import fetch
from google.appengine.api import memcache

from django.utils import simplejson as json
from xml.dom import minidom

import config

class ApiHandler():
  def __init__(self, remote_addr='', parse = False):
    self.parse = parse
    self.remote_addr = remote_addr

  def requestWiki(self, keyword):
    result = memcache.get(keyword, namespace='wiki')
    if not result:
      resp = fetch('http://en.wikipedia.org/w/api.php?action=opensearch&search=%s&limit=10&namespace=0&format=xml' % (keyword))

      if resp and resp.content:
        result = resp.content
        memcache.set(keyword, result, time=config.apiCache, namespace='wiki')

    if self.parse:
      parsed = []
      dom = minidom.parseString(result)
      for item in dom.getElementsByTagName('Item')[0:5]:
        parsed.append({
          'title': self.getDomText(item.getElementsByTagName('Text')[0]),
          'text':  self.getDomText(item.getElementsByTagName('Description')[0]),
          'link':  self.getDomText(item.getElementsByTagName('Url')[0])
        })
      return parsed
    return result

  def requestBing(self, keyword):
    result = memcache.get(keyword, namespace='bing')
    if not result:
      url = 'http://api.search.live.net/json.aspx?Appid=%s&query=%s&sources=web' % (config.BING_KEY, keyword)
      logging.debug('fetching url %s' % (url))
      resp = fetch(url)

      if resp and resp.content:
        result = resp.content.decode('utf-8')
        memcache.set(keyword, result, time=config.apiCache, namespace='bing')

    if self.parse:
      try:
        obj = json.loads(result)
        parsed = []
        for article in obj['SearchResponse']['Web']['Results'][0:5]:
          parsed.append({
            'title': article['Title'],
            'info': '%s, %s' % (article['DisplayUrl'], article['DateTime']),
            'text': article['Description'],
            'link': article['Url']
          })
        return parsed

      except KeyError:
        return False
      except json.JSONDecodeError, e:
        logging.error("API parse error: %s" %(e))
        return False

    return result

  def requestNews(self, keyword):
    result = memcache.get(keyword, namespace='news')
    if not result:
      resp = fetch('http://api.search.live.net/json.aspx?Appid=%s&query=%s&sources=news' % (config.BING_KEY, keyword))

      if resp and resp.content:
        result = unicode(resp.content, 'utf-8')
        memcache.set(keyword, result, time=config.apiCache, namespace='news')

    if self.parse:
      try:
        obj = json.loads(result)
        parsed = []
        for article in obj['SearchResponse']['News']['Results'][0:5]:
          parsed.append({
            'title': article['Title'],
            'info': '%s, %s' % (article['Source'], article['Date']),
            'text': article['Snippet'],
            'link': article['Url']
          })
        return parsed

      except KeyError:
        return False
      except json.JSONDecodeError, e:
        logging.error("API parse error: %s" %(e))
        return False

    return result

  def requestBlogs(self, keyword):
    result = memcache.get(keyword, namespace='blogs')
    if not result:
      resp = fetch('https://ajax.googleapis.com/ajax/services/search/blogs?v=1.0&q=%s&userip=%s' % (keyword, self.remote_addr))

      if resp and resp.content:
        result = unicode(resp.content, 'utf-8')
        memcache.set(keyword, result, time=config.apiCache, namespace='blogs')

    if self.parse:
      try:
        obj = json.loads(result)
        parsed = []
        for article in obj['responseData']['results'][0:5]:
          parsed.append({
            'title': re.sub('<[^>]*>', '', article['title']),
            'info': '<a href="%s">%s</a>, %s' % (article['blogUrl'], article['author'], article['publishedDate']),
            'text': article['content'],
            'link': article['postUrl']
          })
        return parsed

      except KeyError:
        return False
      except json.JSONDecodeError, e:
        logging.error("API parse error: %s" %(e))
        return False

    return result

  def getDomText(self, el):
    text = []
    for child in el.childNodes:
      if child.nodeType == child.TEXT_NODE:
        text.append(child.data)

    return ''.join(text)

class ProxyWiki(webapp.RequestHandler):
  def get(self, keyword=False):
    if not keyword:
      return

    result = ApiHandler().requestWiki(keyword)
    self.response.headers['Content-Type'] = 'text/xml'
    self.response.out.write(result)

class ProxyBing(webapp.RequestHandler):
  def get(self, keyword=False):
    if not keyword:
      return

    result = ApiHandler().requestBing(keyword)
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(result)

class ProxyNews(webapp.RequestHandler):
  def get(self, keyword=False):
    if not keyword:
      return

    result = ApiHandler().requestNews(keyword)
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(result)

class ProxyBlogs(webapp.RequestHandler):
  def get(self, keyword=False):
    if not keyword:
      return

    result = ApiHandler(self.request.remote_addr).requestBlogs(keyword)
    self.response.headers['Content-Type'] = 'application/json'
    self.response.out.write(result)

application = webapp.WSGIApplication(
    [(r'/api/wiki/(.*)', ProxyWiki)
    ,(r'/api/bing/(.*)', ProxyBing)
    ,(r'/api/news/(.*)', ProxyNews)
    ,(r'/api/blogs/(.*)', ProxyBlogs)
    ]
    , debug=True)

def main():
  logging.getLogger().setLevel(logging.DEBUG)
  run_wsgi_app(application)

if __name__ == "__main__":
  main()
