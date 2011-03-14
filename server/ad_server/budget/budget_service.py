# !/usr/bin/env python

# TODO: PLEASE HAVE THIS FIX DJANGO PROBLEMS
# from appengine_django import LoadDjango
# LoadDjango()
# import os
# from django.conf import settings
# 
# os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
# # Force Django to reload its settings.
# settings._target = None
# END TODO: PLEASE HAVE THIS FIX DJANGO PROBLEMS

from google.appengine.api import memcache

from datetime import datetime


def timeslice_memcache_minute_key(campaign_id,datetime):
  return 'timeslice:%s:%s'%(campaign_id,datetime.strftime('%y%m%d%H%M'))

class BudgetService(object):
    """
    A service that determines if a campaign can be shown based upon the defined 
    budget for that campaign. If the budget_type is "evenly", a minute by minute
    sub-budget is kept as well. 
    """

    def __init__(self, campaign_id, daily_budget, timeslices=1440, fudge_factor=0.0, test_mode=False):
        self.campaign_id = campaign_id
        self.remaining_daily_budget = daily_budget
        self.remaining_timeslices = timeslices
        self.fudge_factor = fudge_factor
        self.budget_timeslices = {}
        self.counter = 0
        
        self._set_next_timeslice()

    def _update_budget(self, amount_spent):
        self.budget_timeslices[self.timeslice_name] = self.budget_timeslices[self.timeslice_name] - amount_spent
  
    def _next_timeslice_budget(self):
            return (self.remaining_daily_budget / self.remaining_timeslices) * (1 + self.fudge_factor)
            
    def _set_next_timeslice(self):
        rollover_budget = self._get_timeslice_budget()

        #set new timeslice name
        self.timeslice_name = str(self.campaign_id) + ":" + str(self.counter)
        self.counter += 1
        
        self.budget_timeslices[self.timeslice_name] = rollover_budget + self._next_timeslice_budget()
        
    def _has_budget(self):
        if self._get_timeslice_budget() >= 0:
            return True
        return False
        
    def _get_timeslice_budget(self):
        try:
            return self.budget_timeslices[self.timeslice_name]
        except AttributeError:
            return 0
        
    def process(self, amount_spent):
        """ Return true if the current timeslice has a budget for a given cost"""
        self._update_budget(amount_spent)
        return self._has_budget()
            
        