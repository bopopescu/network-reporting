from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, render_to_string, JSONResponse
from common.utils.timezones import Pacific_tzinfo
# from common.ragendja.auth.decorators import google_login_required as login_required
from budget import budget_service

from advertiser.models import ( Campaign,
                                AdGroup,
                                )
import logging
import datetime

# For taskqueue                                
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp
from advertiser.models import Campaign
from budget.models import NoSpendingForIncompleteLogError, BudgetSlicer

# The constraints: 
# The maximum bucket size is 100
# Each worker must complete in less than a timeslice to avoid contention
CAMPAIGNS_PER_WORKER = 30

def daily_budget_advance(request):
     return budget_advance(request, daily=True)
     
def timeslice_budget_advance(request):
    return budget_advance(request, daily=False)

def budget_advance(request, daily=False):
    campaigns = Campaign.all().filter("budget >", 0).filter("active =", True).fetch(1000000)
    keys = [camp.key() for camp in campaigns]
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
        
        if daily:
            url = reverse('budget_daily_advance_worker')
        else:    
            url = reverse('budget_advance_worker')
        
        taskqueue.add(url=url,
                      queue_name='budget-advance',
                      params={'key_shard': serial_key_shard}
                      )
        
        start_index += CAMPAIGNS_PER_WORKER
        end_index += CAMPAIGNS_PER_WORKER
        
    if daily:
        return HttpResponse('Advanced budget daily: %s' % text)
    else:
        return HttpResponse('Advanced budget timeslices: %s' % text)
    
def daily_advance_worker(request):
    return advance_worker(request,daily=True)

def timeslice_advance_worker(request):
    return advance_worker(request,daily=False)
    
def advance_worker(request, daily=False):
    serial_key_shard = request.POST['key_shard']
    keys = serial_key_shard.split(',')

    for key in keys:
        logging.info(key)

    camps = Campaign.get(keys)
    for camp in camps:
        if daily:
            budget_service.daily_advance(camp)
        else:
            budget_service.timeslice_advance(camp)

    return HttpResponse('Worker Succeeded')


def chart(request, campaign_key):
    camp = Campaign.get(campaign_key)
    
    context =  {'campaign_key': campaign_key,
                'campaign': camp}
    
    return render_to_response(request,'budget/chart.html', context)
    
    

def budget_view(request, adgroup_key):
    adgroup = AdGroup.get(adgroup_key)

    camp = adgroup.campaign
    
    remaining_daily_budget = budget_service.remaining_daily_budget(camp)
    remaining_ts_budget = budget_service.remaining_ts_budget(camp)
        
    today = datetime.datetime.now(Pacific_tzinfo()).date()
    one_month_ago = today - datetime.timedelta(days=30)
    
    daily_logs = budget_service._get_daily_logs_for_date_range(camp,
                                                               one_month_ago,
                                                               today)
                                                                
                                                                
    slicer = BudgetSlicer.get_or_insert_for_campaign(camp)
    ts_logs = slicer.timeslice_logs.order("-end_date").fetch(1440)
        
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
                'clear_memcache_ts_url': clear_memcache_ts_url}



    
    return render_to_response(request,'budget/budget_view.html', context)
    
    
    
    
    