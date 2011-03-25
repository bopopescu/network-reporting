from google.appengine.ext import db
from advertiser.models import Campaign

DEFAULT_TIMESLICES = 1440.0 # Timeslices per day
DEFAULT_FUDGE_FACTOR = 0.1

class BudgetSlicer(db.Model):
    
    campaign = db.ReferenceProperty(Campaign)
    previous_budget_snapshot = db.FloatProperty(default=0.0)
  

    @property
    def timeslice_budget(self):
        return self.campaign.budget / DEFAULT_TIMESLICES * (1.0 + DEFAULT_FUDGE_FACTOR)

    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key', None):
            campaign = kwargs.get('campaign',None)
            if campaign:
                key_name = self.get_key_name(campaign)
        super(BudgetSlicer, self).__init__(parent=parent, key_name=key_name, **kwargs)

    @classmethod
    def get_key_name(cls, campaign):
        if isinstance(campaign,db.Model):
            campaign = campaign.key()
        return "k:"+str(campaign)
        

    @classmethod
    def get_db_key(cls, campaign):
        return Key.from_path(cls.kind(), cls.get_key_name(campaign))
        
    @classmethod
    def get_or_insert_for_campaign(cls,campaign,**kwargs):
        key_name = cls.get_key_name(campaign)
        kwargs.update(campaign=campaign)
        return super(BudgetSlicer,cls).get_or_insert(key_name,**kwargs)
        

class TimesliceLog(db.Model):
      budget_slicer = db.ReferenceProperty(BudgetSlicer,collection_name="timeslice_logs")
      initial_memcache_budget = db.FloatProperty()
      final_memcache_budget = db.FloatProperty()
      end_date = db.DateTimeProperty()
      
      @property
      def spending(self):
          return self.initial_memcache_budget - self.final_memcache_budget