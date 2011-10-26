from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, render_to_string, JSONResponse
from common.utils.timezones import Pacific_tzinfo
# from common.ragendja.auth.decorators import google_login_required as login_required
from advertiser.models import ( Campaign,
                                AdGroup,
                                )
from budget import budget_service
from budget.models import Budget

import logging
import datetime

# For taskqueue
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp

# The constraints:
# The maximum bucket size is 100
# Each worker must complete in less than a timeslice to avoid contention
CAMPAIGNS_PER_WORKER = 30

def budget_advance(request):
    budgets = Budget.all()..filter('active =', True).fetch(1000000)
    #campaigns = Campaign.all().filter("budget >", 0).filter("active =", True).fetch(1000000)
    keys = [budget.key() for budget in budgets]
    count = len(keys)

    # Break keys into shards of 30 and send them to a worker
    start_index = 0
    end_index = CAMPAIGNS_PER_WORKER

    text = ''

    while start_index < count:

        key_shard = keys[start_index:end_index]

        # Add the task to the default queue.

        serial_key_shard = ''
        for key in key_shard:
            serial_key_shard += str(key) + ','

        serial_key_shard = serial_key_shard[:-1]
        text += '<br><br> %s:%s has value: %s' % (start_index, end_index, serial_key_shard)

        # serialization of dict objects fails for params so we do it manually
        # key_shard = [str(key) for key in key_shard]

        taskqueue.add(url=reverse('budget_advance_worker'),
                      queue_name='budget-advance',
                      params={'key_shard': serial_key_shard}
                      )

        start_index += CAMPAIGNS_PER_WORKER
        end_index += CAMPAIGNS_PER_WORKER

    return HttpResponse('Advanced budget timeslices: %s' % text)

def advance_worker(request, daily=False):
    serial_key_shard = request.POST['key_shard']
    keys = serial_key_shard.split(',')

    for key in keys:
        logging.info(key)

    budgets = Budget.get(keys)
    for budg in budgets:
        budget_service.timeslice_advance(budg, budg.testing)

    return HttpResponse('Worker Succeeded')


def chart(request, campaign_key):
    camp = Campaign.get(campaign_key)

    context =  {'campaign_key': campaign_key,
                'campaign': camp}

    return render_to_response(request,'budget/chart.html', context)



def budget_view(request, adgroup_key):
    adgroup = AdGroup.get(adgroup_key)

    budget = adgroup.campaign.budget_obj

    if budget:
        remaining_daily_budget = budget_service.remaining_daily_budget(budget)
        remaining_ts_budget = budget_service.remaining_ts_budget(budget)
        braking_fraction = budget_service.braking_fraction(budget)
    else:
        remaining_ts_budget = None
        remaining_daily_budget = None
        braking_fraction = None

    today = datetime.datetime.now()
    one_month_ago = today - datetime.timedelta(days=30)

    daily_logs = budget_service._get_daily_logs_for_datetime_range(budget,
                                                                   one_month_ago,
                                                                   today)


    slicer = BudgetSlicer.get_or_insert_for_campaign(camp)
    ts_logs = slicer.timeslice_logs.order("-end_date").fetch(DEFAULT_TIMESLICES)

    #### Build budgetslicer address ####
    # prefix = "http://localhost:8080/_ah/admin/datastore/edit?key="
    prefix = "https://appengine.google.com/datastore/edit?app_id=mopub-inc&namespace=&key="

    budget_obj = BudgetSlicer.get_or_insert_for_campaign(camp)
    budget_obj_url = prefix + str(budget_obj.key())


    #### Build memcache clearing urls ####
    # clear_prefix = "http://localhost:8080"
    clear_prefix = "http://app.mopub.com"

    daily_key = budget_service._make_campaign_daily_budget_key(camp)
    ts_key = budget_service._make_campaign_ts_budget_key(camp)

    clear_memcache_daily_url = clear_prefix + "/m/clear?key=" + daily_key + "&namespace=budget"
    clear_memcache_ts_url = clear_prefix + "/m/clear?key=" + ts_key + "&namespace=budget"



    context =  {'campaign': camp,
                'remaining_daily_budget': remaining_daily_budget,
                'remaining_ts_budget': remaining_ts_budget,
                'daily_logs': daily_logs,
                'ts_logs': ts_logs,
                'today': today,
                'one_month_ago': one_month_ago,
                'budget_obj_url': budget_obj_url,
                'clear_memcache_daily_url': clear_memcache_daily_url,
                'clear_memcache_ts_url': clear_memcache_ts_url,
                'braking_fraction': braking_fraction}




    return render_to_response(request,'budget/budget_view.html', context)
