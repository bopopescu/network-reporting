import logging

from common.utils.query_managers import CachedQueryManager

from google.appengine.ext import db

from publisher.models import App
from publisher.models import Site as AdUnit
from advertiser.models import Campaign, AdGroup, Creative
import datetime
from reporting.query_managers import StatsModelQueryManager
from google.appengine.api import memcache

from ad_server.debug_console import trace_logging


class AdUnitContext(object):
    """All the adunit information necessary
    to run the auction. """
    
    @classmethod
    def wrap(cls, adunit):
        """ Factory method that takes an adunit, fetches all the appropriate information
        from the database, and then returns an adunit_context object """
        
        adgroups = cls.fetch_adgroups(adunit)
        campaigns = cls.fetch_campaigns(adgroups)
        creatives = cls.fetch_creatives(adgroups)
        
        adunit_context = cls(adunit, 
                             campaigns, 
                             adgroups, 
                             creatives)
        return adunit_context

    def __init__(self, adunit, campaigns, adgroups, creatives):
        self.adunit = adunit
        
        
        self.campaigns = campaigns
        self.adgroups = adgroups
        self.creatives = creatives
        
        # creative_ctr is a mapping from creative keys to CreativeCTR objects
        self.creative_ctrs = {}
        for c in creatives:
            self.creative_ctrs[c.key()] = CreativeCTR(c, adunit)
            
            
        # Triggers dereferencing of references so we can cache the whole object
        # We ask both Account and App for an arbitrary property 
        self.adunit.account.active
        self.adunit.app_key.active
        
        # We also dereference the network configs
        self.adunit.account.network_config.admob_pub_id
        self.adunit.app.network_config.admob_pub_id
        self.adunit.network_config.admob_pub_id
        


    def _get_ctr(self, creative, date=datetime.date.today(), date_hour=None, min_sample_size=1000):
        '''Given a creative, calculates the CTR.  
        The date_hour parameter is the last full hour that has passed.
        If date_hour is specified, gets or updates the CTR for that hour. 
        If date_hour is not specified, use daily CTR.
        If sample size is insufficient, return None.'''
        
        creative_ctr = self.creative_ctrs.get(creative.key())
        try:
            # Use daily if date_hour is not specified
            if date_hour is not None:
                return creative_ctr.get_or_update_hourly_ctr(date_hour=date_hour, min_sample_size=min_sample_size)
            else:
                return creative_ctr.get_or_update_daily_ctr(date=date, min_sample_size=min_sample_size)
        except AttributeError:
            # If we couldn't find the creative, return None
            return None
                    
    def get_creatives_for_adgroups(self,adgroups,limit=30):
        """ Get only the creatives for the requested adgroups """
        adgroup_keys = [adgroup.key() for adgroup in adgroups]
        creatives = self.creatives
        # we must use get_value_for_datastore so we don't auto dereference
        creatives = [creative for creative in self.creatives
                              if creative.ad_group.key() in adgroup_keys]

        return creatives
        
    @classmethod
    def fetch_adgroups(cls, adunit, limit=50):
        logging.info("getting adgroups from db")
        adgroups = AdGroup.all().filter("site_keys =",adunit.key()).\
                                  filter("deleted =",False).\
                                  fetch(limit)
        return adgroups

    @classmethod
    def fetch_creatives(cls, adgroups, limit=30):
        logging.info("getting creatives from db")
        creatives = Creative.all().filter("ad_group IN", adgroups).\
                    filter("active =",True).filter("deleted =",False).\
                    fetch(limit)
                    
        # re-write creative so that ad_group is actually the object already in memory
        for creative in creatives:
            creative.ad_group = [ag for ag in adgroups 
                        if ag.key() == Creative.ad_group.get_value_for_datastore(creative)][0]
        
        return creatives

    @classmethod
    def fetch_campaigns(cls, adgroups):  
        # campaign exclusions... budget + time
        logging.info("attach eligible campaigns")
        campaigns = []
        for adgroup in adgroups:
            campaign = db.get(adgroup.campaign.key())
            if not campaign.deleted:
                campaigns.append(campaign)
        return campaigns
        
    def key(self):
        """ Since we want a 1-1 mapping from adunits to adunit_contexts, we
        appropriate the key from the adunit, returns a string. """
        return "context:"+str(self.adunit.key())
        
    def get_creative_by_key(self,creative_key):
        creative = None
        for c in self.creatives:
            if str(creative_key) == str(c.key()):
                creative = c
                break
        return creative    
        
class CreativeCTR(object):
    """ The relevant CTR information for a creative-adunit pairing"""
    def __init__(self, creative, adunit):
        self.creative = creative
        self.adunit = adunit
        self.hourly_ctr = None
        self.daily_ctr = None
        self.hourly_ctr_expiration_datetime = None
        self.daily_ctr_expiration_date = None
        
    def get_or_update_hourly_ctr(self, date_hour=datetime.datetime.now(), min_sample_size=1000):
        """ Get's the hourly ctr value, updates it if expired, 
            ctr is defined as clicks/impressions*100
            date_hour is a datetime object"""
        if not self.hourly_ctr_expiration_datetime or \
        date_hour >= self.hourly_ctr_expiration_datetime:
            # Update both the hourly and daily ctrs
            self._update_hourly_ctr(date_hour=date_hour, min_sample_size=min_sample_size)
            # self._update_daily_ctr(date=date_hour.date(), min_sample_size=min_sample_size)

            return self.hourly_ctr

        # If not expired
        return self.hourly_ctr
    
    def _update_hourly_ctr(self, date_hour=datetime.datetime.now(), min_sample_size=1000):

        last_full_hour = date_hour - datetime.timedelta(hours=1)
        # logging.info("Using date: %s, %s, %s" % (last_full_hour, self.adunit, self.creative))
        
        smqm = StatsModelQueryManager(self.adunit.account)

        qm_stats = smqm.get_stats_for_hours(publisher=self.adunit,
                                         advertiser=self.creative,
                                         date_hour=last_full_hour)

        stats = qm_stats # qm_stats is a list of stats of length 1

        # Make sure we have enough impressions
        if stats.impression_count >= min_sample_size:
            self.hourly_ctr = stats.ctr
  
        # Whether or not we updated the ctr, set the new expiration date
        self.hourly_ctr_expiration_datetime = date_hour + datetime.timedelta(hours=1)
    

    def get_or_update_daily_ctr(self, date=datetime.date.today(), min_sample_size=1000):
        """ Get's the daily ctr value, updates it if expired, 
            ctr is defined as clicks/impressions*100"""
        # Do calculations if expired
        if self.daily_ctr_expiration_date is None or date >= self.daily_ctr_expiration_date:
            self._update_daily_ctr(date=date, min_sample_size=min_sample_size)

            # Daily ctr has been updated if possible, return it
            return self.daily_ctr

        # If not expired
        return self.daily_ctr
        

    def _update_daily_ctr(self, date=datetime.date.today(), min_sample_size=1000):
          """ Updates the daily ctr value if we have enough impressions """
          smqm = StatsModelQueryManager(self.adunit.account)

          qm_stats = smqm.get_stats_for_days(publisher=self.adunit,
                                           advertiser=self.creative,
                                           days=[date])

          stats = qm_stats[0] # qm_stats is a list of stats of length 1
          # Make sure we have enough impressions
          if stats.impression_count >= min_sample_size:
              self.daily_ctr = stats.ctr

          # Whether or not we updated the ctr, set the new expiration date
          self.daily_ctr_expiration_date = date
