#Copyright (c) 2012, www.directionalstar.com 

#See the file LICENSE.txt for copying permission.

import logging
import datetime
import operator

from google.appengine.ext import db

import forms

class HotKeywords(db.Model):
  keywords = db.StringListProperty()
  date = db.DateTimeProperty(auto_now_add=True)

class DailyTrends(db.Model):
  keywords = db.StringListProperty()
  date = db.DateProperty()
  ordering = db.StringProperty(choices = set(['latest', 'popular']), default = 'popular')

class FavoriteKeywords(db.Model):
  keywords = db.StringListProperty()
  user = db.UserProperty()

def getFavorites(user):
  return FavoriteKeywords.all().filter('user =', user).get()

def summarizeDailyTrends(date, ordering = False):
  today = datetime.date.today()

  if ordering not in ['latest', 'popular']:
    ordering = False

  if not ordering:
    if date == today:
      ordering = 'latest'
    else:
      ordering = 'popular'

  logging.debug('summarized trends for the day %s requested by %s' % (date.isoformat(), ordering))
  dailyModel = DailyTrends.all().filter('date =', date).filter('ordering =', ordering).get()

  if dailyModel and date != today:
    dailyKeywords = dailyModel.keywords
    source = 'db'
    logging.debug('serving trends from database')

  else:
    query = 'WHERE date > DATETIME(%d, %d, %d, 0, 0, 0) AND date < DATETIME(%d, %d, %d, 23, 59, 59) ORDER BY date DESC' \
      % (date.year, date.month, date.day, \
         date.year, date.month, date.day)

    hotKeywordsList = HotKeywords.gql(query)

    if ordering == 'popular':
      trendList = []
      keywordScores = {}
      for trend in hotKeywordsList:
        if trend.keywords not in trendList:
          trendList.append(trend.keywords)

          for rank, keyword in enumerate(trend.keywords):
            keywordScores[keyword] = keywordScores.get(keyword, 0) + (20 - rank)

      dailyKeywords = map(operator.itemgetter(0), sorted(keywordScores.iteritems(), key=operator.itemgetter(1), reverse=True))

    else:
      trendList = []
      dailyKeywords = []
      for trend in hotKeywordsList:
        if trend.keywords not in trendList:
          trendList.append(trend.keywords)

          for keyword in trend.keywords:
            if keyword not in dailyKeywords:
              dailyKeywords.append(keyword)

    logging.debug('summarized %d keywords' % (len(dailyKeywords)))

    if len(dailyKeywords) and date != today:
      dailyModel = DailyTrends(keywords = dailyKeywords, date = date, ordering = ordering)
      dailyModel.put()

    source = 'sum'

  return {
    'success': True,
    'keywords': dailyKeywords,
    'ordering': ordering,
    'source': source
  }

class JSError(db.Model):
  url = db.StringProperty()
  line = db.StringProperty()
  message = db.StringProperty()
  agent = db.StringProperty()
  date = db.DateTimeProperty(auto_now_add=True)

class UserEvent(db.Model):
  user = db.UserProperty()
  target = db.StringProperty()
  action = db.StringProperty()
  label = db.StringProperty()
  date = db.DateTimeProperty(auto_now_add=True)

class BadgeDef(db.Model):
  target = db.StringProperty()
  action = db.StringProperty()
  after = db.IntegerProperty()
  active = db.BooleanProperty()
  name = db.StringProperty()
  desc = db.TextProperty()
  icon = db.StringProperty()

class UserBadge(db.Model):
  user = db.UserProperty()
  date = db.DateTimeProperty(auto_now_add=True)
  badge = db.ReferenceProperty(BadgeDef)

def checkForBadges(evt):
  newbadges = []

  badges = BadgeDef.all()
  badges.filter('target = ', evt.target)
#  badges.filter('active = ', True)
  logging.debug('counted %d badges with target %s' % (badges.count(),evt.target))
  if badges.count() < 1:
    return newbadges

  events = UserEvent.all()
  events.filter('user = ', evt.user)
  events.filter('target = ', evt.target)
  events.filter('date <= ', evt.date)
  badges.filter('action = ', '')
  logging.debug('counted %d events, %d badges without action' % (events.count(), badges.count()))
  badges.filter('after = ', events.count())
  for badge in badges:
    newbadges.append(badge)

  # resetting badges query
  badges = BadgeDef.all()
  badges.filter('target = ', evt.target)

  events.filter('action = ', evt.action)
  badges.filter('action = ', evt.action)
  logging.debug('counted %d events, %d badges with action %s' % (events.count(), badges.count(), evt.action))
  badges.filter('after = ', events.count())
  for badge in badges:
    newbadges.append(badge)

  return newbadges



# User settings

class UserSettings(db.Model):
  user = db.UserProperty()
  autoupdate = db.BooleanProperty(default=True)

  _editables = {
    'autoupdate': 'bool'
  }

  _labels = {
    'autoupdate': ('Update topic list automatically', 'Check this option if you want the topic list to be refreshed automatically when updates are available.')
  }

  def get(self, name):
    if name not in self._editables:
      logging.error('UserSettings.set(%s): unknown setting' % (name))
      return None

    if self._editables[name] == 'bool':
      return bool(getattr(self, name))
      

  def set(self, name, value):
    if name not in self._editables:
      logging.error('UserSettings.set(%s): unknown setting' % (name))
      return False

    if self._editables[name] == 'bool':
      value = value=='true'
      
    try:
      logging.debug('setting %s: %s -> %s' % (name, getattr(self, name), value))
      setattr(self, name, value)

    except AttributeError, e:
      logging.error('UserSettings.set(%s): unknown setting' % (name))
      return False

    return True

  def update(self, vDict):
    for name, value in vDict.items():
      self.set(name, value)

    self.put()

  def list(self):
    props = {}
    for name, value in self.properties().items():
      if name in self._editables:
        label = self.label(name)
        props[name] = {
          'label':  label[0],
          'help':   label[1],
          'value':  value,
          'type':   self._editables[name],
          'input':  forms.FormInputs(self._editables[name], name, self.get(name)).html()
        }

    return props

  def label(self, name):
    return self._labels.get(name, (name, False))

def getUserSettings(user):
  settings = UserSettings.all().filter('user =', user).get()

  if not settings:
    settings = UserSettings(user = user)
    settings.put()

  return settings
