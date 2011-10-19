from google.appengine.ext import db
from budget.helpers import get_curr_slice_num, get_slice_from_datetime
import logging
import math

#from advertiser.models import Campaign

DEFAULT_FUDGE_FACTOR = 0.005



class Budget(db.Model):

    start_datetime = db.DateTimeProperty(required=True)
    end_datetime = db.DateTimeProperty(required=False)
    active = db.BooleanProperty()
    #campaign = db.ReferenceProperty(Campaign, collection_name = '_budget_obj')

    # All at once, evenly
    delivery_type = db.StringProperty()

    # One of these is set, the other is none
    #
    # Static total is set if it's 
    #  -- total USD, no end date, allatonce
    #  -- total USD, no end date, evenly < --- this case makes 0 sense
    #  -- total USD, end date,    allatonce 
    static_total_budget = db.FloatProperty()

    # Static Slice budget is set if:
    #  -- total USD, end date,    evenly
    #  -- $/day,     end date,    evenly
    #  -- $/day,     end date,    allatonce
    #  -- $/day,     no end date, evenly
    #  -- $/day,     no end date, allatonce
    static_slice_budget = db.FloatProperty()

    total_spent = db.FloatProperty()
    curr_slice = db.IntegerProperty()

    created_at = db.DateTimeProperty(auto_now_add=True)

#    def __init__(self, parent=None, key_name=None, **kwargs):
#        if not key_name and not kwargs.get('key', None):
#            # We are not coming from database
#            campaign = kwargs.get('campaign',None)
#            if campaign:
#                key_name = self.get_key_name(campaign)
#
#        super(Budget, self).__init__(parent=parent,
#                                     key_name=key_name,
#                                     **kwargs)
#
#    @classmethod
#    def get_key_name(cls, campaign):
#        if isinstance(campaign,db.Model):
#            campaign = campaign.key()
#        return "k:"+str(campaign)
#
#    @classmethod
#    def get_by_campaign(cls, campaign):
#        return cls.get_by_key_name(cls.get_key_name(campaign))
#
#    @classmethod
#    def get_db_key(cls, campaign):
#        return Key.from_path(cls.kind(), cls.get_key_name(campaign))
#
#    @classmethod
#    def get_or_insert_for_campaign(cls,campaign,**kwargs):
#        key_name = cls.get_key_name(campaign)
#        kwargs.update(campaign=campaign)
#
#        def _txn(campaign):
#            obj = cls.get_by_campaign(campaign)
#            if not obj:
#                obj = Budget(**kwargs)
#                obj.put()
#            return obj
#        return db.run_in_transaction(_txn,campaign)

    def is_active_for_timeslice(self, slice_num):
        """ Returns True if the campaign is active for this TS
        False otherwise """
        if slice_num is None:
            return False

        if slice_num >= self.start_slice:
            if (self.end_slice and slice_num <= self.end_slice) or self.end_slice is None:
                return True
            else:
                return False
        else:
            return False

    @property
    def total_budget(self):
        """ Returns the total budget this budget has to spend """
        if static_total_budget is not None:
            return static_total_budget
        else:
            return self.static_slice_budget * self.total_slices
        pass

    @property
    def start_slice(self):
        """ Returns the timeslice when this budget begins """
        return get_slice_from_datetime(self.start_datetime)

    @property
    def end_slice(self):
        """ Returns the timeslice when this budget ends """
        if self.end_datetime:
            return get_slice_from_datetime(self.end_datetime)
        else:
            return None

    @property
    def next_slice_budget(self):
        """ Returns the budget for the next timeslice.  This is a 
        function of the appropriate static budget, the total spend,
        and the desired spend """
        difference = self.expected_spent - self.total_spent
        if difference >= 0:
            return (self.static_slice_budget + difference)

    @property
    def expected_spent(self):
        """ Returns the amount the campaign SHOULDVE spent up until now
        Be aware 'now' is actually the most recent timeslice change.  
        So if we eval @ the start of a timeslice and then a few minutes
        later this should be the same
        """
        if self.static_total_budget:
            # The static_total_budget cases that make sense are all
            # all at once, which means they've spent as much as they
            # should've at all times
            return self.total_spent
        elapsed_slices = self.curr_slice - self.start_slice
        expected = self.static_slice_budget * elapsed_slices
        return expected

    @property
    def total_slices(self):
        """ Number of slices this budget spans """
        if self.end_slice:
            return self.end_slice - self.start_slice + 1
        else:
            return None

    @property
    def remaining_slices(self):
        """ Number of slices until this budget is finished """
        if self.end_slice:
            return (self.end_slice - get_curr_slice_num() + 1)
        else:
            return None

    @property
    def remaining_budget(self):
        """ Returns the amount of money this budget has left to spend """
        return self.total_budget - self.total_spent

    @property
    def last_slice_log(self):
        """ Returns the most recent slicelog for this budget """
        try:
            return self.timeslice_logs.order('-slice_num').get()
        except:
            return None



class BudgetSliceLog(db.Model):
    """ SliceLogs aren't really imported as slicelogs (they are, but not REALLY) as much
    as they are important as Memcache snapshots.  They basically have the last known good
    MC configuration and are used if shit hits the fan """

    budget = db.ReferenceProperty(Budget, collection_name = 'timeslice_logs')
    slice_num = db.IntegerProperty(required = True)

    desired_spending = db.FloatProperty()

    ######### MC SNAPSHOT #############
   
    # total spending of whole budget when this TS is init'd
    prev_total_spending = db.FloatProperty()
    # Braking fraction as computed for this timeslice
    prev_braking_fraction = db.FloatProperty(default=1.0)


    ######### Part that is actually a log ########
    
    # How much was actually spent
    actual_spending = db.FloatProperty()

    @property
    def final_total_spending(self):
        """ Total spending of this TS and all previous """
        return self.prev_total_spending + self.actual_spending

    @property
    def remaining_spending(self):
        """ The amount of money this TS had to spend less what it spent (can be negative!) """
        return self.desired_spending - self.actual_spending

    @classmethod
    def get_current_for_campaign(cls, campaign):
        """ Gets the curret slicelog for the given campaign """
        curr_slice = get_curr_slice_num()
        pass

    @classmethod
    def get_slice_log_by_campaign_ts(cls, campaign, timeslice):
        """ Gets the slicelogs by campaign and slice_num """

    #TODO: Custom init stuff, k:ts_log:<camp>:<slice>

