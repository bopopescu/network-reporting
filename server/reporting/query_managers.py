from common.utils.cachedquerymanager import CachedQueryManager

from google.appengine.ext import db

from reporting.models import SiteStats

class SiteStatsQueryManager(CachedQueryManager):
    def get_sitestats_for_days(self, site=None, owner=None, days=[]):
        if isinstance(site,db.Model):
          site_key = site.key()
        else:
          site_key = site
        if isinstance(owner,db.Model):
          owner_key = owner.key()
        else:
          owner_key = owner
        keys = (SiteStats.get_key(site_key, owner_key, d) for d in days)
        stats = SiteStats.get(keys) # db get
        stats = [s or SiteStats() for s in stats]
        return stats