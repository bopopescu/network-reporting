from google.appengine.ext import db
from advertiser.models import Campaign
import logging
import math

DEFAULT_TIMESLICES = 1440 # Timeslices per day
DEFAULT_FUDGE_FACTOR = 0.005


###### INTERIM VERSION TO BE DELETED #######

class BudgetSlicer(db.Model):
    
    campaign = db.ReferenceProperty(Campaign)

    # New Models
    spent_today = db.FloatProperty(default = 0.)
    spent_in_campaign = db.FloatProperty(default = 0.)
    current_timeslice = db.IntegerProperty(default = 0)
    
    @property
    def timeslice_budget(self):
        """ The amount to increase the remaining_timeslice_budget amount by
        every minute or so. This is how much we want to spend on this budget """
        remaining_timeslice = DEFAULT_TIMESLICES-self.current_timeslice
        remaining_budget = self.campaign.budget - self.spent_today
        return remaining_budget / remaining_timeslice * (1.0 + DEFAULT_FUDGE_FACTOR)
    
    def set_timeslice(self, seconds):
        self.current_timeslice = int(math.floor((DEFAULT_TIMESLICES*seconds)/86400))
    
    def advance_timeslice(self):
        self.current_timeslice = int((self.current_timeslice+1)%DEFAULT_TIMESLICES)
    
    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key', None):
            # We are not coming from database
            campaign = kwargs.get('campaign',None)
            if campaign:
                key_name = self.get_key_name(campaign)
                    
        super(BudgetSlicer, self).__init__(parent=parent,
                                           key_name=key_name,
                                            **kwargs)

    @classmethod
    def get_key_name(cls, campaign):
        if isinstance(campaign,db.Model):
            campaign = campaign.key()
        return "k:"+str(campaign)
        
    @classmethod
    def get_by_campaign(cls, campaign):
        return cls.get_by_key_name(cls.get_key_name(campaign))
        

    @classmethod
    def get_db_key(cls, campaign):
        return Key.from_path(cls.kind(), cls.get_key_name(campaign))
        
    @classmethod
    def get_or_insert_for_campaign(cls,campaign,**kwargs):
        key_name = cls.get_key_name(campaign)
        kwargs.update(campaign=campaign)
        
        def _txn(campaign):
            obj = cls.get_by_campaign(campaign)
            if not obj:
                obj = BudgetSlicer(**kwargs)
                obj.put()
            return obj
        return db.run_in_transaction(_txn,campaign)        




class BudgetSliceLog(db.Model):
      budget_obj = db.ReferenceProperty(BudgetSlicer,collection_name="timeslice_logs")
      remaining_daily_budget = db.FloatProperty()
      end_date = db.DateTimeProperty()
      
      # New Models
      actual_spending = db.FloatProperty()
      desired_spending = db.FloatProperty()
    
class BudgetDailyLog(db.Model):
    budget_obj = db.ReferenceProperty(BudgetSlicer,collection_name="daily_logs")
    initial_daily_budget = db.FloatProperty()
    remaining_daily_budget = db.FloatProperty()
    date = db.DateProperty()
    
    # New Models
    actual_spending = db.FloatProperty()

    @property
    def spending(self):
        try:
            # If actual_spending is None, calculate it
            return self.actual_spending or (self.initial_daily_budget - 
                                            self.remaining_daily_budget)
        except TypeError:
            raise NoSpendingForIncompleteLogError

class NoSpendingForIncompleteLogError(Exception):
    """ We cannot get spending for logs that are incomplete.
        This should only occur for today, the day in progress. """
    pass