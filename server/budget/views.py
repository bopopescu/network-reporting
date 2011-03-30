from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, render_to_string, JSONResponse

# from common.ragendja.auth.decorators import google_login_required as login_required
from common.utils.decorators import whitelist_login_required
from budget import budget_service

from advertiser.models import ( Campaign,
                                AdGroup,
                                )
# For taskqueue                                
from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.ext import webapp
from advertiser.models import Campaign
import logging


# The constraints: 
# The maximum bucket size is 100
# Each worker must complete in less than a timeslice to avoid contention
CAMPAIGNS_PER_WORKER = 30

def daily_budget_advance(request):
     return budget_advance(request, daily=True)
     
def timeslice_budget_advance(request):
    return budget_advance(request, daily=False)

def budget_advance(request, daily=False):
    keys = Campaign.all(keys_only=True).fetch(1000000)
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
        if camp.budget is not None:
            if daily:
                budget_service.daily_advance(camp)
            else:
                budget_service.timeslice_advance(camp)

    return HttpResponse('Worker Succeeded')


def log_data(request, campaign_key):
    
    camp = Campaign.get(campaign_key)
    
    recent_logs = budget_service.log_generator(camp).order('-end_date').fetch(60)
    log_array = [log.spending for log in recent_logs]
    
    # put in order of least to most recent
    log_array.reverse()
    
    return HttpResponse(simplejson.dumps(log_array))
    
def chart(request, campaign_key):
    camp = Campaign.get(campaign_key)
    
    context =  {'campaign_key': campaign_key,
                'campaign': camp}
    
    return render_to_response(request,'budget/chart.html', context)