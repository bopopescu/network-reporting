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

def budget_advance(request):
    keys = Campaign.all(keys_only=True).fetch(1000000)
    count = len(keys)

    # Break keys into shards of 10 and send them to a worker
    start_index = 0
    end_index = CAMPAIGNS_PER_WORKER
    
    text = ""
    
    while start_index < count:
    
        key_shard = keys[start_index:end_index]
        text += "<br><br> %s:%s has value: %s" % (start_index, end_index, key_shard)
        
        # Add the task to the default queue.
        
        serial_key_shard = ""
        for key in key_shard:
            serial_key_shard += str(key) + ","

        serial_key_shard = serial_key_shard[:-1]
        
        # serialization of dict objects fails for params so we do it manually
        # key_shard = [str(key) for key in key_shard]
        
        taskqueue.add(url=reverse('budget_advance_worker'),
                      queue_name='budget-advance',
                      params={'key_shard': serial_key_shard}
                      )
        
        start_index += CAMPAIGNS_PER_WORKER
        end_index += CAMPAIGNS_PER_WORKER
    
    return HttpResponse("Advanced budget timeslices: %s" % text)
    
def advance_worker(request):
    serial_key_shard = request.POST['key_shard']
    keys = serial_key_shard.split(',')
    
    for key in keys:
        logging.info(key)

    camps = Campaign.get(keys)
    for camp in camps:
        if camp.budget is not None:
            budget_service.advance_timeslice(camp)
               
    return HttpResponse("Worker Succeeded")

    
def budget_logs(request, campaign_key):
    
    recent_logs = budget_service.log_generator_from_key(campaign_key)[0]
    output = ""
    
    for log in recent_logs:
        output += str(log) + "\n"
        
    return HttpResponse(recent_logs)
    

    
def mem_budget(request, campaign_key):
    
    campaign = Campaign.get(campaign_key)
    mem_budget =  budget_service._get_budget(campaign)
    
    return HttpResponse(campaign.name + ": " + str(mem_budget))
    
def set_budget(request, campaign_key):
    
    campaign = Campaign.get(campaign_key)
    mem_budget = 100.0
    budget_service._set_memcache(campaign, mem_budget)
    return HttpResponse(campaign.name + ": " + str(mem_budget))