import logging, os, re, datetime, hashlib

import urllib
urllib.getproxies_macosx_sysconf = lambda: {}
from urllib import urlencode

from google.appengine.api import users, memcache
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.db import djangoforms

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from common.ragendja.template import render_to_response, JSONResponse

# from common.ragendja.auth.decorators import google_login_required as login_required
from common.utils.decorators import whitelist_login_required


from publisher.models import Site, Account, App
from publisher.forms import SiteForm, AppForm
from advertiser.models import Campaign, AdGroup, HtmlCreative
from reporting.models import SiteStats

from common.utils.views import RequestHandler
 

class DashBoardHandler(RequestHandler):
  def get(self):
    start_date = datetime.date.today() - datetime.timedelta(days=14)
    stats = SiteStats.gql("where date > :1 order by date desc", start_date).fetch(1000)
    
    # calculate unique active placements (ad slots) and accounts (users)
    # plus accumulate total impression and click counts
    unique_placements = {}
    unique_accounts = {}
    totals = {}
    
    # go and do it
    for s in stats:
      if s.site:
        # add this site stats to the total for the day
        a = totals.get(str(s.date)) or SiteStats(date=s.date)
        a.impression_count += s.impression_count
        a.click_count += s.click_count
        totals[str(s.date)] = a
      
        # add a hash key for the site key and account key to calculate uniques
        unique_placements[s.site.key()] = s.site
        unique_accounts[s.site.account.key()] = s.site.account
      
    # organize daily stats
    total_stats = totals.values()
    total_stats.sort(lambda x,y: cmp(x.date,y.date))
    
    # make a graph
    # url = "http://chart.apis.google.com/chart?cht=lc&chs=800x200&chd=t:%s&chds=0,%d&chxr=1,0,%d&chxt=x,y&chxl=0:|%s&chco=006688&chm=o,006688,0,-1,6|B,EEEEFF,0,0,0" % (
    #    ','.join(map(lambda x: str(x.impression_count), total_stats)), 
    #    max(map(lambda x: x.impression_count, total_stats)) * 1.5,
    #    max(map(lambda x: x.impression_count, total_stats)) * 1.5,
    #    '|'.join(map(lambda x: x.date.strftime("%m/%d"), total_stats)))
    url = ''  
    # organize placements
    placements = unique_placements.values()
    for p in placements:
      p.stats = models.SiteStats(site=p)
      p.stats.impression_count = sum(map(lambda x: x.impression_count, filter(lambda x: x.site and x.site.key() == p.key(), stats)))
      p.stats.click_count = sum(map(lambda x: x.click_count, filter(lambda x: x.site and x.site.key() == p.key(), stats)))
    placements.sort(lambda x,y: cmp(y.stats.impression_count, x.stats.impression_count))
    
    # thanks
    return render_to_response(self.request,'bizops/dashboard.html', 
      {"stats": total_stats, 
        "chart_url": url,
        "impression_count": sum(map(lambda x: x.impression_count, total_stats)),
        "click_count": sum(map(lambda x: x.click_count, total_stats)),
        "ctr": 0.0,
        "unique_placements": unique_placements, 
        "unique_accounts": unique_accounts, 
        "placements": placements})

@whitelist_login_required
def dashboard(request,*args,**kwargs):
  return DashBoardHandler()(request,*args,**kwargs) 
