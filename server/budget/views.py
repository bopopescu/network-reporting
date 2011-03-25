from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, render_to_string, JSONResponse

# from common.ragendja.auth.decorators import google_login_required as login_required
from common.utils.decorators import whitelist_login_required
from budget import budget_service

def budget_advance(request):
    budget_service.advance_all()
    return HttpResponse("Advanced budget timeslices.")
    
def budget_logs(request, campaign_key):
    
    recent_logs = budget_service.log_generator_from_key(campaign_key)[0]
    output = ""
    
    for log in recent_logs:
        output += str(log) + "\n"
        
    return HttpResponse(recent_logs)
    
def mem_budget(request, campaign_key):
    current_memory_budget = budget_service._get_budget_from_key(campaign_key)
    return HttpResponse(current_memory_budget)