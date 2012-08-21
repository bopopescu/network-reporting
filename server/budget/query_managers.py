import logging
import urllib
import urllib2

from google.appengine.ext import db

from datetime import datetime, timedelta

from budget.models import BudgetChangeLog, Budget, BudgetSliceLog, BudgetSlicer
from common.utils.tzinfo import Pacific, utc
from common.utils.query_managers import QueryManager

from budget.helpers import (build_budget_update_string,
                            get_slice_from_datetime,
                            parse_budget_update_string)

from adserver_constants import (BUDGET_UPDATE_URL,
                                ADSERVER_ADMIN_HOSTNAME,
                                ADSERVER_STAGING_HOSTNAME,
                                ADSERVER_TESTING_HOSTNAME)
from advertiser.query_managers import AdGroupQueryManager

ZERO_BUDGET = 0.0
ONE_DAY = timedelta(days=1)
BUDGET_UPDATE_DATE_FMT = '%Y/%m/%d %H:%M'

#TODO(tornado): This needs to be a url that we'll actually use
ADSERVER = 'adserver.mopub.com'
TEST_ADSERVER = 'localhost:8000'


class BudgetQueryManager(QueryManager):

    Model = Budget

    @classmethod
    def update_or_create_budgets_for_adgroup_keys(
            cls, adgroup_keys, total_spent=0.0, testing=False, fetcher=None,
            migrate_total=False):
        adgroups = AdGroupQueryManager.get(adgroup_keys)
        for adgroup in adgroups:
            cls.update_or_create_budget_for_adgroup(
                adgroup, total_spent=total_spent, testing=False, fetcher=None,
                migrate_total=False)

        # Use db.put() instead of AdGroupQueryManager.put(). The latter calls
        # this method, which would cause an infinite loop!
        db.put(adgroups)

    @classmethod
    def update_or_create_budget_for_adgroup(cls, ag, total_spent=0.0,
                                            testing=False, staging=False,
                                            fetcher=None, migrate_total=False):
        # Update budget
        if ag.start_datetime is None:
            ag.start_datetime = datetime.utcnow()
        elif str(ag.start_datetime.tzinfo) == str(Pacific):
            ag.start_datetime = ag.start_datetime.astimezone(utc).replace(tzinfo=None)
        if ag.end_datetime and str(ag.end_datetime.tzinfo) == str(Pacific):
            ag.end_datetime = ag.end_datetime.astimezone(utc).replace(tzinfo=None)

        if ag.start_datetime:
            remote_start = ag.start_datetime.strftime(BUDGET_UPDATE_DATE_FMT)
        else:
            remote_start = None
        if ag.end_datetime:
            remote_end = ag.end_datetime.strftime(BUDGET_UPDATE_DATE_FMT)
        else:
            remote_end = None
        remote_update_dict = dict(adgroup_key=str(ag.key()),
                                  start_datetime=remote_start,
                                  end_datetime=remote_end,
                                  static_total_budget=ag.full_budget,
                                  static_daily_budget=ag.daily_budget,
                                  active=ag.active,
                                  delivery_type=ag.budget_strategy)
        if ag.has_daily_budget:
            remote_update_dict['static_total_budget'] = None
        elif ag.has_full_budget:
            remote_update_dict['static_daily_budget'] = None
        if migrate_total:
            remote_update_dict['total_spent'] = ag.budget_obj.total_spent
        qs = urllib.urlencode(remote_update_dict)
        update_uri = BUDGET_UPDATE_URL + '?' + qs

        if testing and fetcher:
            fetcher.fetch(update_uri)
            return True
        else:
            pass
            #TODO(tornado): THIS IS COMMENTED OUT, NEED TO IMPLEMENT
            # WHEN SHIT IS LIVE FOR REAL
            try:
                if staging:
                    adserver_url = ADSERVER_STAGING_HOSTNAME
                elif testing:
                    adserver_url = ADSERVER_TESTING_HOSTNAME
                else:
                    adserver_url = ADSERVER_ADMIN_HOSTNAME
                full_url = 'http://' + adserver_url + update_uri
                logging.info('Updating budget at ' + full_url)
                urllib2.urlopen(full_url)
                return True
            except Exception, e:
                # This isn't implemented yet
                #TODO(tornado): need to implement this and things
                logging.warn("Couldn't update budget: " + str(e))
                return False
                

    @classmethod
    def migrate_adgroup(cls, adgroup):
        if adgroup.budget_obj:
            return
        adgroup, budget = cls.test_migrate(adgroup)
        adgroup.budget_obj = budget
        adgroup.put()

    @classmethod
    def test_migrate(cls, adgroup):
        now = datetime.now().date()
        start = adgroup.start_date
        end = adgroup.end_date
        slicer = BudgetSlicer.get_by_adgroup(adgroup)
        if slicer is not None:
            spent_today = slicer.spent_today
            spent_in_ag = slicer.spent_in_adgroup
        else:
            spent_today = 0.0
            spent_in_ag = 0.0
        print spent_today
        print spent_in_ag
        total_spent = spent_today + spent_in_ag
        if start is None:
            if adgroup.budget is not None or adgroup.full_budget is not None:
                start = now
        if start:
            # make it the start of the day if it's a start date
            adgroup.start_datetime = datetime(start.year, start.month, start.day, 0, tzinfo = Pacific)
        if end:
            # make it the end of the day if it's an end date
            adgroup.end_datetime = datetime(end.year, end.month, end.day, 23, 59, 0, tzinfo = Pacific)
        print "Total spent1: %s" % total_spent
        if not total_spent:
            total_spent = 0.0
        print "Total spent2: %s" % total_spent
        budget = cls.update_or_create_budget_for_adgroup(adgroup, total_spent = total_spent)
        if budget is not None:
            budget.put()
            if spent_today:
                todays_log = BudgetSliceLog(budget = budget,
                                            slice_num = get_slice_from_datetime(now),
                                            desired_spending = spent_today,
                                            actual_spending = spent_today,
                                            prev_total_spending = spent_in_ag,
                                            prev_braking_fraction = 1.0,
                                            )
                todays_log.put()
            if spent_in_ag:
                all_prev_logs = BudgetSliceLog(budget = budget,
                                               slice_num = get_slice_from_datetime(now - ONE_DAY),
                                               desired_spending = spent_in_ag,
                                               actual_spending = spent_in_ag,
                                               prev_total_spending = 0.0,
                                               prev_braking_fraction = 1.0,
                                               )
                all_prev_logs.put()
        print budget
        return adgroup, budget

    @classmethod
    def prep_update_budget(cls, budget,
                           start_datetime = None,
                           end_datetime = False,
                           delivery_type = None,
                           static_total_budget = None,
                           static_slice_budget = None,
                           ):
        """ Flags the budget to be updated, sets it's update
        string appropriately """
        if end_datetime is False:
            end_datetime = budget.end_datetime
        if start_datetime is None:
            start_datetime = budget.start_datetime
        if delivery_type is None:
            delivery_type = budget.delivery_type

        # if either of these are set, then override the previous, otherwise use prev
        if static_total_budget is None and static_slice_budget is None:
            static_total_budget = budget.static_total_budget
            static_slice_budget = budget.static_slice_budget

        update_str = build_budget_update_string(start_datetime, end_datetime, delivery_type, static_total_budget, static_slice_budget)
        budget.update = True
        budget.update_str = update_str
        budget.put()
        return

    @classmethod
    def exec_update_budget(cls, budget):
        """ Takes the update string, applies all the updates, logs the change """

        new_start, new_end, new_delivery, new_static_total, new_static_slice = parse_budget_update_string(budget.update_str)

        change_log = BudgetChangeLog(start_datetime      = budget.start_datetime,
                                     end_datetime        = budget.end_datetime,
                                     static_total_budget = budget.static_total_budget,
                                     static_slice_budget = budget.static_slice_budget,
                                     delviery_type      = budget.delivery_type,
                                     budget             = budget,
                                     )
        change_log.put()


        budget.start_datetime = new_start
        budget.end_datetime = new_end
        budget.delivery_type = new_delivery
        budget.static_total_budget = new_static_total
        budget.static_slice_budget = new_static_slice

        budget.update_str = None
        budget.update = False
        budget.put()
