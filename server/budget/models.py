from google.appengine.ext import db
from budget.helpers import get_curr_slice_num, get_slice_from_datetime, TS_PER_DAY, TEST_TS_PER_DAY
import logging
import math

#from advertiser.models import Campaign

DEFAULT_FUDGE_FACTOR = 0.005

SUCCESSFUL_DELIV_PER = .95


class Budget(db.Model):

    start_datetime = db.DateTimeProperty(required=False)#True)
    end_datetime = db.DateTimeProperty(required=False)
    active = db.BooleanProperty()
    #campaign = db.ReferenceProperty(Campaign, collection_name = '_budget_obj')

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

    def __repr__(self):
        return "Budget(Start: %s, End: %s, Delivery_type: %s, Static_budget: %s, Static_slice_budget: %s, total_spent: %s, curr_slice: %s, curr_date: %s" % (self.start_datetime, self.end_datetime, self.delivery_type, self.static_total_budget, self.static_slice_budget, self.total_spent, self.curr_slice, self.curr_date)

    @property
    def is_active(self):
        return self.is_active_for_timeslice(self.curr_slice)

    def is_active_for_date(self, dte):
        return self.is_active_for_datetime(dte)

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
                return expected - self.spent_today

        # This is a total budget
        elif self.static_total_budget:
            return expected - self.total_spent

        # This is a fucked up situation
        else:
            logging.error("Budget has no budget.....?")

    @property
    def slice_budget(self):
        """ Returns static_slice_budget or DYNAMIC slice_budget """

        # if we have a static slice budget, just spend that shit
        if self.static_slice_budget:
            return self.static_slice_budget

        elif self.finite and self.static_total_budget:
            return self.static_total_budget / self.total_slices
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
        day_start_slice = get_slice_from_datetime(self.curr_date, self.testing)
        keys = BudgetSliceLog.get_keys_for_slices(self, xrange(day_start_slice, self.curr_slice))
        todays_logs = BudgetSliceLog.get(keys)
        tot = 0.0
        for log in todays_logs:
            if log and log.actual_spending is not None:
                tot += log.actual_spending
        return tot


    ######################## NOTE ###############################
    #   This is why I want to make budgets immutable,
    #   If you change the daily budget, then the 'expected_spent'
    #   value is going to be WAY off, even though it's not really.
    #   If, instead, the old budget were gotten rid of and a new budget
    #   were created, all budgets would have the appropriate expected
    #   spending.
    #############################################################
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
            return self.end_slice - self.start_slice + 1
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
            return self.timeslice_logs.order('-slice_num').get()
        except:
            return None

    @property
    def most_recent_slice_log(self):
        """ Returns the most recent slicelog for this budget """
        try:
            # Get the two most recent, the most recent will ALWAYS be incomplete
            return self.timeslice_logs.order('-slice_num').fetch(2)[1]
        except:
            return None



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


class BudgetChangeLog(db.Model):
    start_datetime = db.DateTimeProperty()
    end_datetime = db.DateTimeProperty()

    delivery_Type = db.StringProperty()
    static_total_budget = db.FloatProperty()
    static_slice_budget = db.FloatProperty()
    budget = db.ReferenceProperty(Budget, collection_name = 'change_logs')


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

    #TODO: Custom init stuff, k:ts_log:<camp>:<slice>


