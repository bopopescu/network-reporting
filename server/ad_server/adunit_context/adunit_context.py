from google.appengine.ext import db
from google.appengine.api.images import InvalidBlobKeyError

from publisher.models import Site as AdUnit
from advertiser.models import AdGroup, Creative
import datetime
from reporting.query_managers import StatsModelQueryManager
from google.appengine.api import memcache
from common.utils.db_deep_get import deep_get_from_db
from simple_models import SimpleAdUnitContext



from ad_server.debug_console import trace_logging

from common.constants import MAX_OBJECTS
from common.utils import helpers


class AdUnitContext(object):
    """All the adunit information necessary
    to run the auction. """
    
    def simplify(self):
        return SimpleAdUnitContext(self.adunit, self.campaigns, self.adgroups, self.creatives)
 
    @classmethod
    def wrap(cls, adunit):
        """ Factory method that takes an adunit, fetches all the appropriate information
        from the database, and then returns an adunit_context object """
        if isinstance(adunit, str):
            adunit = AdUnit.get(adunit)
        
        adgroups = cls.fetch_adgroups(adunit)
        creatives = cls.fetch_creatives(adunit, adgroups)
        # Fetch all the references so we can cache the whole object
        deep_get_from_db([adunit] + adgroups + creatives)
        campaigns = cls.collect_campaigns(adgroups)
        
        adunit_context = cls(adunit, 
                             campaigns, 
                             adgroups, 
                             creatives)
        return adunit_context

    def __init__(self, adunit, campaigns, adgroups, creatives):
        # For high performance, the Model instances passed as arguments should be deeply-fetched (e.g. using deep_get_from_db()).
        
        self.adunit = adunit
        
        self.campaigns = campaigns
        self.adgroups = adgroups
        self.creatives = creatives
        self.creative_ctrs = {}
        for c in creatives:
            self.creative_ctrs[c.key()] = CreativeCTR(c, adunit)
            
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
                    
    def get_creatives_for_adgroups(self,adgroups,limit=MAX_OBJECTS):
        """ Get only the creatives for the requested adgroups """
        adgroup_keys = set(adgroup.key() for adgroup in adgroups)
        # creative.ad_group should have already been fetched, so we don't need to worry about avoiding auto-dereferencing it.
        creatives = [creative for creative in self.creatives
                              if creative.ad_group.key() in adgroup_keys]
        return creatives
        
    @classmethod
    def fetch_adgroups(cls, adunit, limit=MAX_OBJECTS):
        trace_logging.info("getting adgroups from db")
        adgroups = AdGroup.all().filter("site_keys =",adunit.key()).\
                                  filter("deleted =",False).\
                                  fetch(limit)
        return [adgroup for adgroup in adgroups if adgroup.active]

    @classmethod
    def fetch_creatives(cls, adunit, adgroups, limit=MAX_OBJECTS):
        trace_logging.info("getting creatives from db")
        creatives = Creative.all().filter("account =", adunit.account.key()).\
                    filter("active =",True).filter("deleted =",False)
                    # fetch(limit)
        # creatives = Creative.all().filter("ad_group IN", adgroups).\
        #             filter("active =",True).filter("deleted =",False).\
        #             fetch(limit)
        adgroup_keys = set(adgroup.key() for adgroup in adgroups)
 
        def adgroup_key(creative):
            # Returns the creative.ad_group.key() without fetching the ad_group
            return Creative.ad_group.get_value_for_datastore(creative)

        # Return only the creatives that reference one of our adgroups.
        return [c for c in creatives if adgroup_key(c) in adgroup_keys]

    @classmethod
    def collect_campaigns(cls, adgroups):
        # For high performance, the campaigns should already be fetched.
        campaigns_by_key = {}
        for adgroup in adgroups:
            campaigns_by_key[adgroup.campaign.key()] = adgroup.campaign
        return [c for c in campaigns_by_key.itervalues() if not c.deleted] 
                    


    @classmethod
    def _get_image_url(cls, creative):
        if not hasattr(creative, 'image_blob'):
            return ""
        if not creative.image_blob:
            return ""

        image_url = creative.image_serve_url
        if image_url: return image_url

        try:
            image_url = helpers.get_url_for_blob(creative.image_blob,
                                                 ssl=False)
        except InvalidBlobKeyError:
            trace_logging.error("Could not find blobkey. "\
                       "Perhaps you are on mopub-experimental.")
            image_url = ""
        except NotImplementedError:
            image_url = "http://localhost:8080/_ah/img/blobby"
        return image_url

    @classmethod
    def fetch_campaigns(cls, adgroups):  
        # TODO(simon): Remove this function? Remove the campaigns attribute entirely?
        trace_logging.info("getting campaigns from db")

        def campaign_key(adgroup):
            # Returns the adgroup.campaign.key() without fetching the campaign
            return AdGroup.campaign.get_value_for_datastore(adgroup)

        campaign_keys = set(campaign_key(adgroup) for adgroup in adgroups)
        # Batch get all the relevant campaigns
        campaigns = db.get(list(campaign_keys))
        campaigns = [c for c in campaigns if not c.deleted] 
        return campaigns   
        
    @classmethod
    def key_from_adunit_key(cls, adunit_key):    
        """ Since we want a 1-1 mapping from adunits to adunit_contexts, we
        appropriate the key from the adunit, returns a string. """
        return "context:" + str(adunit_key)
        
    def key(self):
        """ Uses the adunit's key """
        return AdUnitContext.key_from_adunit_key(self.adunit.key())

        
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
                                           days=[date],
                                           use_mongo=False)

          stats = qm_stats[0] # qm_stats is a list of stats of length 1
          # Make sure we have enough impressions
          if stats.impression_count >= min_sample_size:
              self.daily_ctr = stats.ctr

          # Whether or not we updated the ctr, set the new expiration date
          self.daily_ctr_expiration_date = date
