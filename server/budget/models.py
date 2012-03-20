from google.appengine.ext import db
from budget.helpers import get_curr_slice_num, get_slice_from_datetime, TS_PER_DAY, TEST_TS_PER_DAY
from common.utils.tzinfo import utc, Pacific
import logging
import math
import sys, logging
#modules = sorted([k for k in sys.modules])
#for m in modules:
#    logging.warning("K: %s\t\tV: %s" % (m, sys.modules[m]))

from datetime import datetime, timedelta, date


# increase numbers by the slighest amount because floating pt errors tend to yield numbers JUST less
# than what we want (999.9999999999999 instead of 1000)
FLOAT_FUDGE_FACTOR = 1.000000001

SUCCESSFUL_DELIV_PER = .95

JUST_UNDER_ONE_DAY = timedelta(minutes = 1439)

class BudgetSlicer(db.Model):

    campaign = db.ReferenceProperty()

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


class Budget(db.Model):

    start_datetime = db.DateTimeProperty(required=True)
    end_datetime = db.DateTimeProperty(required=False)
    active = db.BooleanProperty()

    # All at once, evenly
    delivery_type = db.StringProperty(choices = ['evenly', 'allatonce'])

    # One of these is set, the other is none
    #
    # Static total is set if it's
    #  -- total USD, no end date, allatonce
    #  -- total USD, no end date, evenly < --- this case makes 0 sense
    #  -- total USD, end date,    allatonce
    #  -- total USD, end date,    evenly
    static_total_budget = db.FloatProperty()

    # Static Slice budget is set if:
    #  -- $/day,     end date,    evenly
    #  -- $/day,     no end date, evenly
    #  -- $/day,     no end date, allatonce
    #  -- $/day,     end date,    allatonce
    static_slice_budget = db.FloatProperty()

    total_spent = db.FloatProperty(default=0.0)
    curr_slice = db.IntegerProperty(default=0)
    curr_date = db.DateProperty()

    created_at = db.DateTimeProperty(auto_now_add=True)

    testing = db.BooleanProperty(default = False)

    # If a budget is changed, dont' change it until the NEXT TS Advance.
    # update is a flag, the str is the next state to put it in
    update = db.BooleanProperty(default = False)
    update_str = db.StringProperty()
    day_tz = db.StringProperty()

    @property
    def next_day_hour(self):
        return self._next_day_hour.time()

    def __repr__(self):
        return "Budget(Start: %s, End: %s, Delivery_type: %s, Static_budget: %s, Static_slice_budget: %s, total_spent: %s, curr_slice: %s, curr_date: %s" % (self.start_datetime, self.end_datetime, self.delivery_type, self.static_total_budget, self.static_slice_budget, self.total_spent, self.curr_slice, self.curr_date)

    @property
    def is_active(self):
        return self.is_active_for_timeslice(self.curr_slice)

    def is_active_for_date(self, dte):
        temp = datetime(dte.year, dte.month, dte.day) + JUST_UNDER_ONE_DAY
        return self.is_active_for_datetime(temp)

    def is_active_for_datetime(self, dtetime):
        return self.is_active_for_timeslice(get_slice_from_datetime(dtetime, self.testing))

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
    def finite(self):
        if self.start_datetime and self.end_datetime:
            return True
        else:
            return False

    @property
    def total_budget(self):
        """ Returns the total budget this budget has to spend
            if total_budget or end_datetime is set,
            returns None otherwise
        """
        if self.static_total_budget:
            return self.static_total_budget

        elif self.total_slices:
            return self.static_slice_budget * self.total_slices
        else:
            return None

    @property
    def start_slice(self):
        """ Returns the timeslice when this budget begins """
        return get_slice_from_datetime(self.start_datetime, self.testing)

    @property
    def end_slice(self):
        """ Returns the timeslice when this budget ends
            if end_datetime is set, returns None otherwise
         """
        if self.end_datetime:
            return get_slice_from_datetime(self.end_datetime, self.testing)
        else:
            return None

    @property
    def remaining_slices(self):
        if not self.finite:
            return False
        return (self.end_slice - self.curr_slice) + 1

    @property
    def next_slice_budget(self):
        """ Don't return a negative slice budget, return 0 """
        return max(self._next_slice_budget, 0.0)

    @property
    def _next_slice_budget(self):
        """ Returns the budget for the next timeslice.  This is a
        function of the appropriate static budget, the total spend,
        and the desired spend """
        expected = self.expected_spent
        # This is a daily budget
        if self.static_slice_budget:
            # This is finite
            if self.finite:
                return expected - self.total_spent

            # This is unending
            else:
                spent_today = self.spent_today
                return expected - spent_today

        # This is a total budget
        elif self.static_total_budget:
            return expected - self.total_spent

        # This is a fucked up situation
        else:
            logging.error("Budget has no budget.....?")

    @property
    def slice_budget(self):
        """ Returns static_slice_budget or slice_budget
        as a function of total and the number of slices """

        # if we have a static slice budget, just spend that shit
        if self.static_slice_budget:
            if self.testing:
                return self.static_slice_budget
            else:
                if self.testing:
                    return self.static_slice_budget
                else:
                    return self.static_slice_budget * FLOAT_FUDGE_FACTOR

        elif self.finite and self.static_total_budget:
            if self.testing:
                return (self.static_total_budget / self.total_slices)
            else:
                if self.testing:
                    return (self.static_total_budget / self.total_slices)
                else:
                    return (self.static_total_budget / self.total_slices) * FLOAT_FUDGE_FACTOR
        else:
            return self.static_total_budget

    @property
    def daily_budget(self):
        """ Should only be used by static_budget w/ aao
            Returns static_slice_budget * slices in a day
        """
        if self.static_total_budget and self.delivery_type == 'allatonce':
            return self.static_total_budget

        if self.testing:
            return self.slice_budget * TEST_TS_PER_DAY
        else:
            return self.slice_budget * TS_PER_DAY

    @property
    def spent_today(self):
        """ Computes the amount spent today from the slicelogs
            Uses curr_date and curr_slice to determine which logs to get
        """
        # If this budget hasn't been init'd, don't return anything
        if not (self.curr_date and self.curr_slice):
            return 0.0
        day_start_slice = get_slice_from_datetime(self.curr_date, self.testing)
        keys = BudgetSliceLog.get_keys_for_slices(self, xrange(day_start_slice, self.curr_slice))
        todays_logs = BudgetSliceLog.get(keys)
        tot = 0.0
        for log in todays_logs:
            if log and log.actual_spending is not None:
                tot += log.actual_spending
        return tot


    @property
    def expected_spent(self):
        """ Returns the amount the campaign SHOULDVE spent up until now
        Be aware 'now' is actually the most recent timeslice change.
        So if we eval @ the start of a timeslice and then a few minutes
        later this should be the same
        """
        if self.static_total_budget:

            if self.delivery_type == 'allatonce':
                return self.static_total_budget
            else:
                return self.slice_budget * self.elapsed_slices

        elif self.static_slice_budget:
            if self.finite:
                if self.delivery_type == 'allatonce':
                    return self.daily_budget * self.elapsed_days
                else:
                    return self.slice_budget * self.elapsed_slices

            else:
                if self.delivery_type == 'allatonce':
                    # Don't roll over on days
                    return self.daily_budget
                else:
                    return self.slice_budget * self.elapsed_slices_today
        else:
            logging.error("Can't compute expected spent without a budget...?")
            pass

    @property
    def total_slices(self):
        """ Number of slices this budget spans """
        if self.end_slice:
            slices = self.end_slice - self.start_slice + 1
            if slices == 0:
                logging.warning("Start: %s End: %s" % (self.start_datetime, self.end_datetime))
                slices = 1
            return slices
        else:
            return None

    @property
    def elapsed_slices(self):
        """ Number of slices that have elapsed """
        # curr - start + 1 because current slice counts as having happened
        return (self.curr_slice - self.start_slice) + 1

    @property
    def elapsed_slices_today(self):
        """ Number of slices that have elapsed """

        # curr - start_today + 1 because current slice counts as having happened
        return (self.curr_slice - get_slice_from_datetime(self.curr_date, self.testing)) + 1


    @property
    def elapsed_days(self):
        """ Number of days that have elapsed """

        # curr - start + 1 because current day counts as having happened
        return (self.curr_date - self.start_datetime.date()).days + 1

    @property
    def remaining_budget(self):
        """ Returns the amount of money this budget has left to spend """
        return self.total_budget - self.total_spent

    @property
    def last_slice_log(self):
        """ Returns the most recent slicelog for this budget """
        try:
            current = BudgetSliceLog.get(BudgetSliceLog.get_key(self, self.curr_slice))
            return current
        except:
            return None

        #try:
        #    return self.timeslice_logs.order('-slice_num').get()
        #except:
        #    return None

    @property
    def most_recent_slice_log(self):
        """ Returns the most recent slicelog for this budget """
        try:
            old = BudgetSliceLog.get(BudgetSliceLog.get_key(self, self.curr_slice - 1))
            return old
        except:
            return None

        #try:
            # Get the two most recent, the most recent will ALWAYS be incomplete
        #    return self.timeslice_logs.order('-slice_num').fetch(2)[1]
        #except:
        #    return None



    def increase_total_budget(self, incr):
        """ Increases the total budget by incr
            Returns: True if success
                     False if something was wrong
        """
        incr = float(incr)
        # Static total, trivial
        if self.static_total_budget:
            self.static_total_budget += incr
            return True
        # Slice total, do some magic here
        elif self.finite:
            new_total = self.total_budget + incr
            self.static_slice_budget = new_total / self.total_slices
            return True
        # Can't set the total budget if we have a slice budget
        # and the campaign isn't finite....
        else:
            return False

    def set_total_budget(self, total):
        """ Sets total budget TO total
            Returns: True if success
                     False if something was wrong
        """
        total = float(total)
        if self.static_total_budget:
            self.static_total_budget = total
            return True
        # Slice total, do some magic here
        elif self.finite:
            self.static_slice_budget = total / self.total_slices
            return True
        # Can't set the total budget if we have a slice budget
        # and the campaign isn't finite....
        else:
            return False

    def increase_daily_budget(self, incr):
        """ Increases the daily budget by incr
            Returns: True if success
                     False if something was wrong
        """
        incr = float(incr)
        if self.static_total_budget:
            if self.finite and self.delivery_type == 'evenly':
                pass
            else:
                # DURRRRRR
                return False
        else:
            new_daily = self.daily_budget + incr
            if self.testing:
                self.static_slice_budget = new_daily / TEST_TS_PER_DAY
            else:
                self.static_slice_budget = new_daily / TS_PER_DAY
            return True

    def set_total_daily_budget(self, total):
        """ Sets total daily budget TO total
            Returns: True if success
                     False if something was wrong
        """
        total = float(total)
        if self.static_total_budget:
            if self.finite and self.delivery_type == 'evenly':
                pass
            else:
                # DURRRRRR
                return False
        else:
            if self.testing:
                self.static_slice_budget = total / TEST_TS_PER_DAY
            else:
                self.static_slice_budget = total / TS_PER_DAY
            return True

class BudgetSliceCounter(db.Model):
    """ The global count, maintain slice state for all budgets """
    slice_num = db.IntegerProperty()
    last_synced_slice = db.IntegerProperty()

    @property
    def unsynced_slices(self):
        return slice_num - last_synced_slice

class BudgetSliceSyncStatus(db.Model):
    slice_num = db.IntegerProperty()
    synced = db.BooleanProperty(default=False)


class BudgetChangeLog(db.Model):
    start_datetime = db.DateTimeProperty()
    end_datetime = db.DateTimeProperty()

    delivery_type = db.StringProperty()
    static_total_budget = db.FloatProperty()
    static_slice_budget = db.FloatProperty()
    budget = db.ReferenceProperty(Budget, collection_name = 'change_logs')

    created_at = db.DateTimeProperty(auto_now_add=True)


class BudgetSliceLog(db.Model):
    """ SliceLogs aren't really important as slicelogs (they are, but not REALLY) as much
    as they are important as Memcache snapshots.  They basically have the last known good
    MC configuration and are used if shit hits the fan """

    #Fields for migrations
    budget_obj = db.ReferenceProperty(BudgetSlicer,collection_name="timeslice_logs")
    end_date = db.DateTimeProperty()

    budget = db.ReferenceProperty(Budget, collection_name = 'timeslice_logs')
    slice_num = db.IntegerProperty(required = True, default=0)

    desired_spending = db.FloatProperty()

    ######### MC SNAPSHOT #############

    # total spending of whole budget when this TS is init'd
    prev_total_spending = db.FloatProperty()
    # Braking fraction as computed for this timeslice
    prev_braking_fraction = db.FloatProperty(default=1.0)


    ######### Part that is actually a log ########

    # How much was actually spent
    actual_spending = db.FloatProperty()

    ########################## USED FOR SYNCING
    # Has this log been synced FROM gae TO EC2
    gae_synced = db.BooleanProperty(default=False)

    # Has this log been sycned WITH EC2 data TO GAE
    ec2_synced = db.BooleanProperty(default=False)
    ec2_spending = db.FloatProperty(default=0.0)


    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key', None):
            budget = kwargs.get('budget', None)
            slice_num = kwargs.get('slice_num', None)
            if budget and slice_num:
                key_name = self.get_key_name(budget, slice_num)
        return super(BudgetSliceLog, self).__init__(parent=parent,
                                                    key_name = key_name,
                                                    **kwargs)
    def __repr__(self):
        return "BSliceLog(Slice: %s, Des. Spend: %s, Act. Spend: %s, Prev Spend: %s, Prev Brake: %s)" % (self.slice_num, self.desired_spending, self.actual_spending, self.prev_total_spending, self.prev_braking_fraction)

    @property
    def sync_spending(self):
        if self.ec2_synced:
            return self.actual_spending - self.ec2_spending
        else:
            return self.actual_spending

    @property
    def final_total_spending(self):
        """ Total spending of this TS and all previous """
        return self.prev_total_spending + self.actual_spending

    @property
    def remaining_spending(self):
        """ The amount of money this TS had to spend less what it spent (can be negative!) """
        return self.desired_spending - self.actual_spending

    @property
    def osi(self):
        osi_rate = self.desired_spending * SUCCESSFUL_DELIV_PER
        osi = self.actual_spending >= osi_rate
        return osi
    
    @property
    def pace(self):
        budget = self.budget
        if not budget.is_active_for_date(date.today()): return None
        logging.warn("Has budget")

        last_slice = budget.most_recent_slice_log
        percent_days = budget.elapsed_slices / float(budget.total_slices)
        if budget.delivery_type == "allatonce":
            if budget.static_slice_budget and not budget.end_datetime:
                return ["Delivery", min(1, last_slice.actual_spending / last_slice.desired_spending)]
            else:
                return ["Delivery", min(1, (budget.total_spent / budget.total_budget))]
        else:
            if budget.end_datetime:
                return ["Pacing", min(1, ((budget.total_spent / budget.total_budget) / percent_days))]
            else:
                return ["Pacing", min(1, last_slice.actual_spending / last_slice.desired_spending)]
        return None

    @classmethod
    def get_key_name(cls, budget, slice_num):
        if isinstance(budget, db.Model):
            budget = str(budget.key())
        return 'k:%s:%s' % (budget, slice_num)

    @classmethod
    def get_key(cls, budget, slice_num):
        return db.Key.from_path(cls.kind(), cls.get_key_name(budget, slice_num))

    @classmethod
    def get_slice_log_by_budget_ts(cls, budget, timeslice):
        """ Gets the slicelogs by budget and slice_num """
        pass

    @classmethod
    def get_keys_for_slices(cls, budget, slices):
        for slice_num in slices:
            yield cls.get_key(budget, slice_num)

