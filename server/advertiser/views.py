import logging, os, re, datetime, hashlib

from urllib import urlencode
from copy import deepcopy

import base64, binascii
from google.appengine.api import users, images
from google.appengine.api.urlfetch import fetch
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.core.urlresolvers import reverse
from django.utils import simplejson
from common.ragendja.template import render_to_response, render_to_string, JSONResponse

# from common.ragendja.auth.decorators import google_login_required as login_required
from common.utils.decorators import whitelist_login_required

from advertiser.models import *
from advertiser.forms import CampaignForm, AdGroupForm, \
                             BaseCreativeForm, TextCreativeForm, \
                             ImageCreativeForm, TextAndTileCreativeForm, \
                             HtmlCreativeForm

from publisher.models import Site, Account, App
from reporting.models import StatsModel

from common.utils.query_managers import CachedQueryManager
from common.utils.request_handler import RequestHandler

from account.query_managers import AccountQueryManager
from advertiser.query_managers import CampaignQueryManager, AdGroupQueryManager, \
                                      CreativeQueryManager, TextCreativeQueryManager, \
                                      ImageCreativeQueryManager, TextAndTileCreativeQueryManager, \
                                      HtmlCreativeQueryManager
from publisher.query_managers import AdUnitQueryManager, AppQueryManager, AdUnitContextQueryManager
from reporting.query_managers import StatsModelQueryManager
from budget import budget_service


class AdGroupIndexHandler(RequestHandler):
    def get(self):
        # Set start date if passed in, otherwise get most recent days
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range)
            
        apps = AppQueryManager.get_apps(account=self.account, alphabetize=True)
        
        
        
        campaigns = CampaignQueryManager.get_campaigns(account=self.account)
        if campaigns:
            adgroups = AdGroupQueryManager().get_adgroups(campaigns=campaigns)
        else:
            adgroups = []
    
        for adgroup in adgroups:
            # get stats for date range
            adgroup.all_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(advertiser=adgroup, days=days)
            # get total for the range
            adgroup.stats = reduce(lambda x, y: x+y, adgroup.all_stats, StatsModel())
            adgroup.percent_delivered = budget_service.percent_delivered(adgroup.campaign)
            
            # get targeted apps
            adgroup.targeted_app_keys = []
            for adunit_key in adgroup.site_keys:
                adunit = Site.get(adunit_key)
                if adunit:
                    adgroup.targeted_app_keys.append(adunit.app_key.key())
                # apps.append(adunit.app_key)
            

        promo_campaigns = filter(lambda x: x.campaign.campaign_type in ['promo'], adgroups)
        promo_campaigns = sorted(promo_campaigns, lambda x,y: cmp(y.bid, x.bid))
    
        guarantee_campaigns = filter(lambda x: x.campaign.campaign_type in ['gtee_high', 'gtee_low', 'gtee'], adgroups)
        guarantee_campaigns = sorted(guarantee_campaigns, lambda x,y: cmp(y.bid, x.bid))
        levels = ('high', '', 'low')
        gtee_str = "gtee_%s"
        gtee_levels = []
        for level in levels:
            this_level = gtee_str % level if level else "gtee"
            name = level if level else 'normal'
            level_camps = filter(lambda x:x.campaign.campaign_type == this_level, guarantee_campaigns)
            gtee_levels.append(dict(name = name, adgroups = level_camps))

        for level in gtee_levels:
            if level['name'] == 'normal' and len(gtee_levels[0]['adgroups']) == 0 and len(gtee_levels[2]['adgroups']) == 0: 
                level['foo'] = True 
            elif len(level['adgroups']) > 0:
                level['foo'] = True 
            else:
                level['foo'] = False 

        network_campaigns = filter(lambda x: x.campaign.campaign_type in ['network'], adgroups)
        network_campaigns = sorted(network_campaigns, lambda x,y: cmp(y.bid, x.bid))
    
        backfill_promo_campaigns = filter(lambda x: x.campaign.campaign_type in ['backfill_promo'], adgroups)
        backfill_promo_campaigns = sorted(backfill_promo_campaigns, lambda x,y: cmp(y.bid, x.bid))
    
        adgroups = sorted(adgroups, key=lambda adgroup: adgroup.stats.impression_count, reverse=True)
    
        help_text = None
        if network_campaigns:
            if not (self.account.adsense_pub_id or self.account.admob_pub_id):
                help_text = 'Provide your ad network publisher IDs on the <a href="%s">account page</a>'%reverse('account_index')

        graph_adgroups = adgroups[0:4]
        if len(adgroups) > 4:
            graph_adgroups[3] = AdGroup(name='Others')
            graph_adgroups[3].all_stats = [reduce(lambda x, y: x+y, stats, StatsModel()) for stats in zip(*[c.all_stats for c in adgroups[3:]])]      

        return render_to_response(self.request, 
                                 'advertiser/adgroups.html', 
                                  {'adgroups':adgroups,
                                   'graph_adgroups': graph_adgroups,
                                   'start_date': days[0],
                                   'date_range': self.date_range,
                                   'apps' : apps,
                                   'totals': reduce(lambda x, y: x+y.stats, adgroups, StatsModel()),
                                   'today': reduce(lambda x, y: x+y, [c.all_stats[-1] for c in graph_adgroups], StatsModel()),
                                   'yesterday': reduce(lambda x, y: x+y, [c.all_stats[-2] for c in graph_adgroups], StatsModel()),
                                   'gtee': gtee_levels, 
                                   'promo': promo_campaigns,
                                   'network': network_campaigns,
                                   'backfill_promo': backfill_promo_campaigns,
                                   'account': self.account,
                                   'helptext':help_text })

@whitelist_login_required     
def adgroups(request,*args,**kwargs):
    return AdGroupIndexHandler()(request,*args,**kwargs)


class CreateCampaignAJAXHander(RequestHandler):
    TEMPLATE    = 'advertiser/forms/campaign_create_form.html'
    def get(self,campaign_form=None,adgroup_form=None,
                             campaign=None,adgroup=None):
        if adgroup:                     
            campaign = campaign or adgroup.campaign
        campaign_form = campaign_form or CampaignForm(instance=campaign)
        adgroup_form = adgroup_form or AdGroupForm(instance=adgroup)
        networks = [["admob","AdMob",False],["adsense","AdSense",False],["brightroll","BrightRoll",False],["greystripe","GreyStripe",False],\
            ["iAd","iAd",False],["inmobi","InMobi",False],["jumptap","Jumptap",False],["millennial","Millennial Media",False],["mobfox","MobFox",False],['custom', 'Custom Network', False]]

        all_adunits = AdUnitQueryManager.get_adunits(account=self.account)

        adgroup_form['site_keys'].choices = all_adunits # needed for validation TODO: doesn't actually work

        # TODO: Remove this hack to place the bidding info with the rest of campaign
        #Hackish part
        campaign_form.bid    = adgroup_form['bid']
        campaign_form.bid_strategy = adgroup_form['bid_strategy']
        campaign_form.custom_html = adgroup_form['custom_html']

        adunit_keys = adgroup_form['site_keys'].value or []
        adunit_str_keys = [unicode(k) for k in adunit_keys]
        for adunit in all_adunits:
            adunit.checked = unicode(adunit.key()) in adunit_str_keys

        if adgroup_form:
            for n in networks:
                if adgroup_form['network_type'].value == n[0]:
                    n[2] = True
        elif adgroup:    
            for n in networks:
                if adgroup.network_type == n[0]:
                    n[2] = True
        else:
            networks[0][2] = True # select the first by default            

        campaign_form.add_context(dict(networks=networks))
        adgroup_form.add_context(dict(all_adunits=all_adunits))
        return self.render(campaign_form=campaign_form,adgroup_form=adgroup_form)

    def render(self,template=None,**kwargs):
        template_name = template or self.TEMPLATE
        return render_to_string(self.request,template_name=template_name,data=kwargs)

    def json_response(self,json_dict):
        return JSONResponse(json_dict)

    def post(self):
        adgroup_key = self.request.POST.get('adgroup_key')
        if adgroup_key:
            adgroup = AdGroupQueryManager.get(adgroup_key)
            campaign = adgroup.campaign
        else:
            adgroup = None
            campaign = None

        campaign_form = CampaignForm(data=self.request.POST,instance=campaign)
        adgroup_form = AdGroupForm(data=self.request.POST,instance=adgroup)

        # We pre-emptively clear the cache for site keys, as they may be updated
        adunits_to_update = set()
        if adgroup:
            adunits_to_update.update(adgroup.site_keys)
            
        all_adunits = AdUnitQueryManager.get_adunits(account=self.account)
        sk_field = adgroup_form.fields['site_keys']
        sk_field.choices = all_adunits # TODO: doesn't work needed for validation

        json_dict = {'success':False,'html':None}

        if campaign_form.is_valid():
            campaign = campaign_form.save(commit=False)
            campaign.u = self.account.user
            campaign.account = self.account

            if adgroup_form.is_valid():
                adgroup = adgroup_form.save(commit=False)
                adgroup.account = self.account

                # TODO: clean this up in case the campaign succeeds and the adgroup fails
                CampaignQueryManager.put(campaign)
                adgroup.campaign = campaign
                # TODO: put this in the adgroup form
                if not adgroup.campaign.campaign_type == 'network':
                    adgroup.network_type = None


             #put adgroup so creative can have a reference to it
                AdGroupQueryManager.put(adgroup)

             ##Check if creative exists for this network type, if yes
             #update, if no, delete old and create new
                if campaign.campaign_type == "network":
                    html_data = None
                    if adgroup.network_type == 'custom':
                        html_data = adgroup_form['custom_html'].value
                    #build default creative with custom_html data if custom or none if anything else
                    creative = adgroup.default_creative(html_data)
                    if adgroup.net_creative and creative.__class__ == adgroup.net_creative.__class__:
                        #if the adgroup has a creative AND the new creative and old creative are the same class, 
                        #ignore the new creative and set the variable to point to the old one
                        creative = adgroup.net_creative
                        if adgroup.network_type == 'custom':
                            #if the network is a custom one, the creative might be the same, but the data might be new, set the old
                            #creative to have the (possibly) new data
                            creative.html_data = html_data
                    elif adgroup.net_creative:
                        #in this case adgroup.net_creative has evaluated to true BUT the class comparison did NOT.    
                        #at this point we know that there was an old creative AND it's different from the old creative so
                        #and delete the old creative just marks as deleted!
                        CreativeQueryManager.put(adgroup.net_creative)
                        
                    #creative should now reference the appropriate creative (new if different, old if the same, updated old if same and custom)
                    creative.account = self.account
                    #put the creative so we can reference it
                    CreativeQueryManager.put(creative)
                    #set adgroup to reference the correct creative
                    adgroup.net_creative = creative.key()
                    #put the adgroup again with the new (or old) creative reference
                    AdGroupQueryManager.put(adgroup)

                # Delete Cache. We leave this in views.py because we 
                # must delete the adunits that the adgroup used to have as well
                adunits_to_update.update(adgroup.site_keys)
                if adunits_to_update:
                    adunits = AdUnitQueryManager.get(adunits_to_update)
                    AdUnitContextQueryManager.cache_delete_from_adunits(adunits)

                # Onboarding: user is done after they set up their first campaign
                if self.account.status == "step4":
                    self.account.status = ""
                    AccountQueryManager.put_accounts(self.account)

                json_dict.update(success=True,new_page=reverse('advertiser_adgroup_show',kwargs={'adgroup_key':str(adgroup.key())}))
                return self.json_response(json_dict)

        new_html = self.get(campaign_form=campaign_form,
                                                adgroup_form=adgroup_form)
        json_dict.update(success=False,html=new_html)        
        return self.json_response(json_dict)    

@whitelist_login_required     
def campaign_adgroup_create_ajax(request,*args,**kwargs):
    return CreateCampaignAJAXHander()(request,*args,**kwargs)      


# Wrapper for the AJAX handler
class CreateCampaignHandler(RequestHandler):
    def get(self,campaign_form=None, adgroup_form=None, adgroup_key=None):
        adgroup = None
        if adgroup_key:
            adgroup = AdGroupQueryManager.get(adgroup_key)
            if not adgroup:
                raise Http404("AdGroup does not exist")

        campaign_create_form_fragment = CreateCampaignAJAXHander(self.request).get(adgroup=adgroup)
        return render_to_response(self.request,'advertiser/new.html', {"adgroup_key": adgroup_key,
            "adgroup":adgroup,
            "campaign_create_form_fragment": campaign_create_form_fragment})

@whitelist_login_required         
def campaign_adgroup_create(request,*args,**kwargs):
    return CreateCampaignHandler()(request,*args,**kwargs)         

class CreateAdGroupHandler(RequestHandler):
    def get(self, campaign_key=None, adgroup_key=None, edit=False, title="Create an Ad Group"):
        if campaign_key:
            c = AdGroupQueryManager.get(campaign_key)
            adgroup = AdGroup(name="%s Ad Group" % c.name, campaign=c, bid_strategy="cpm", bid=10.0, percent_users=100.0)
        if adgroup_key:
            adgroup = AdGroupQueryManager.get(adgroup_key)
            c = adgroup.campaign
            if not adgroup:
                raise Http404("AdGroup does not exist")    
        adgroup.budget = c.budget # take budget from campaign for the time being
        f = AdGroupForm(instance=adgroup)
        adunits = AdUnitQueryManager.get_adunits(account=self.account)

        # allow the correct sites to be checked
        for adunit in adunits:
            adunit.checked = adunit.key() in adgroup.site_keys

        # TODO: Clean up this hacked shit 
        networks = [["admob","AdMob",False],["adsense","AdSense",False],["brightroll","BrightRoll",False],["jumptap","Jumptap",False],["greystripe","GreyStripe",False],["iAd","iAd",False],["inmobi","InMobi",False],["millennial","Millennial Media",False],["mobfox","MobFox",False]]
        for n in networks:
            if adgroup.network_type == n[0]:
                n[2] = True

        return render_to_response(self.request,'advertiser/new_adgroup.html', {"f": f, "c": c, "sites": adunits, "title": title, "networks":networks})

    def post(self, campaign_key=None,adgroup_key=None, edit=False, title="Create an Ad Group"):

        adgroup = AdGroupQueryManager.get(adgroup_key)
        campaign = adgroup.campaign

        campaign_form = CampaignForm(data=self.request.POST,instance=campaign)
        adgroup_form = AdGroupForm(data=self.request.POST,instance=adgroup)

        all_adunits = AdUnitQueryManager.get_adunits(account=self.account)

        if campaign_form.is_valid():
            campaign = campaign_form.save(commit=False)
            campaign.u = self.account.user
            campaign.account = self.account

            if adgroup_form.is_valid():
                adgroup = adgroup_form.save(commit=False)
                # TODO: clean this up in case the campaign succeeds and the adgroup fails
                CampaignQueryManager.put(campaign)
                adgroup.campaign = campaign
                AdGroupQueryManager.put(adgroup)
                return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':str(adgroup.key())}))

@whitelist_login_required         
def campaign_adgroup_new(request,*args,**kwargs):
    return CreateAdGroupHandler()(request,*args,**kwargs)            

@whitelist_login_required
def campaign_adgroup_edit(request,*args,**kwargs):
    kwargs.update(title="Edit Ad Group",edit=True)
    return CreateAdGroupHandler()(request,*args,**kwargs)    

class PauseHandler(RequestHandler):
    def post(self):
        action = self.request.POST.get("action", "pause")
        updated_campaigns = []
        for id_ in self.request.POST.getlist('id') or []:
            c = CampaignQueryManager.get(id_)
            updated_campaigns.append(c)
            update_objs = []
            if c != None and c.u == self.account.user:
                if action == "pause":
                    c.active = False
                    c.deleted = False
                    update_objs.append(c)
                elif action == "resume":
                    c.active = True
                    c.deleted = False
                    update_objs.append(c)
                elif action == "delete":
                    # 'deletes' adgroups and creatives
                    c.active = False
                    c.deleted = True
                    update_objs.append(c)
                    for adgroup in c.adgroups:
                        adgroup.deleted = True
                        update_objs.append(adgroup)
                        for creative in adgroup.creatives:
                            creative.deleted = True
                            update_objs.append(creative)
            if update_objs: 
                db.put(update_objs)     
                adgroups = AdGroupQueryManager().get_adgroups(campaigns=updated_campaigns)
                adunits = []
                for adgroup in adgroups:
                    adunits.extend(adgroups.site_keys)
                adunits = AdUnitQueryManager.get(adunits)    
                CachedQueryManager().put(adunits)
        return HttpResponseRedirect(reverse('advertiser_campaign',kwargs={}))

@whitelist_login_required
def campaign_pause(request,*args,**kwargs):
    return PauseHandler()(request,*args,**kwargs)

class ShowAdGroupHandler(RequestHandler):
    def post(self, adgroup_key):
        adgroup = AdGroupQueryManager.get(adgroup_key)
        opt = self.params.get('action')
        update = False
        if opt == 'play':
            adgroup.active = True
            update = True
        elif opt == 'pause':
            adgroup.active = False
            update = True
        elif opt == "delete":   
            adgroup.deleted = True
            AdGroupQueryManager.put(adgroup)
            # TODO: Flash a message saying we deleted the campaign
            return HttpResponseRedirect(reverse('advertiser_campaign'))
            
        else:
            logging.error("Passed an impossible option")

        if update:
            AdGroupQueryManager.put(adgroup)
        return HttpResponseRedirect(reverse('advertiser_adgroup_show', kwargs={'adgroup_key': str(adgroup.key())}))

    def get(self, adgroup_key):
        # Set start date if passed in, otherwise get most recent days
        if self.start_date:
            days = StatsModel.get_days(self.start_date, self.date_range)
        else:
            days = StatsModel.lastdays(self.date_range)

        # Load the ad group itself
        adgroup = AdGroupQueryManager.get(adgroup_key)
        adgroup.all_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(advertiser=adgroup, days=days)
        adgroup.stats = reduce(lambda x, y: x+y, adgroup.all_stats, StatsModel())    
        adgroup.percent_delivered = budget_service.percent_delivered(adgroup.campaign)
    
        # Load creatives and populate
        creatives = CreativeQueryManager.get_creatives(adgroup=adgroup)
        creatives = list(creatives)
        for c in creatives:
            c.all_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(advertiser=c, days=days)
            c.stats = reduce(lambda x, y: x+y, c.all_stats, StatsModel())
            if not c.format:
                c.format = "320x50" # TODO: Should fix DB so that format is always there
            c.size = c.format.partition('x')
    
        # Load all adunits that this thing is targeting right now 
        adunits = AdUnitQueryManager.get_adunits(keys=adgroup.site_keys)
        apps = {}
        for au in adunits:
            app = apps.get(au.app_key.key())
            if not app:
                app = AppQueryManager.get(au.app_key.key())
                app.adunits = [au]
                if app.icon:
                    app.icon_url = "data:image/png;base64,%s" % binascii.b2a_base64(app.icon)
                apps[au.app_key.key()] = app
            else:
                app.adunits += [au]

            au.all_stats = StatsModelQueryManager(self.account,offline=self.offline).get_stats_for_days(publisher=au,advertiser=adgroup, days=days)
            au.stats = reduce(lambda x, y: x+y, au.all_stats, StatsModel())

        # Figure out the top 4 ad units for the graph
        adunits = sorted(adunits, key=lambda adunit: adunit.stats.impression_count, reverse=True)
        graph_adunits = adunits[0:4]
      
        if len(adunits) > 4:
              graph_adunits[3] = Site(name='Others')
              graph_adunits[3].all_stats = [reduce(lambda x, y: x+y, stats, StatsModel()) for stats in zip(*[au.all_stats for au in adunits[3:]])]

        # Load creatives if we are supposed to 
        if not adgroup.network_type:  
            # In order to have add creative
            creative_handler = AddCreativeHandler(self.request)
            creative_fragment = creative_handler.get() # return the creative fragment

            # In order to have each creative be editable
            for c in creatives:
                c.html_fragment = creative_handler.get(creative=c)
        else:
            creative_fragment = None    
    
        # In order to make the edit page
        campaign_create_form_fragment = CreateCampaignAJAXHander(self.request).get(adgroup=adgroup)
    
        return render_to_response(self.request, 'advertiser/adgroup.html', 
                                    {'campaign': adgroup.campaign,
                                    'apps': apps.values(),
                                    'adgroup': adgroup, 
                                    'creatives': creatives,
                                    'totals': reduce(lambda x, y: x+y.stats, adunits, StatsModel()),
                                    'today': reduce(lambda x, y: x+y, [a.all_stats[-1] for a in graph_adunits], StatsModel()),
                                    'yesterday': reduce(lambda x, y: x+y, [a.all_stats[-2] for a in graph_adunits], StatsModel()),
                                    'graph_adunits': graph_adunits,
                                    'start_date': days[0],
                                    'end_date': days[-1],
                                    'creative_fragment':creative_fragment,
                                    'campaign_create_form_fragment':campaign_create_form_fragment})
    
@whitelist_login_required   
def campaign_adgroup_show(request,*args,**kwargs):    
    return ShowAdGroupHandler()(request,*args,**kwargs)


class PauseAdGroupHandler(RequestHandler):
    def post(self):
        action = self.request.POST.get("action", "pause")
        adgroups = []
        update_objs = []
        for id_ in self.request.POST.getlist('id') or []:
            a = AdGroupQueryManager.get(id_)
            adgroups.append(a)
            if a != None and a.campaign.u == self.account.user:
                if action == "pause":
                    a.active = False
                    a.deleted = False
                    update_objs.append(a)
                elif action == "resume":
                    a.active = True
                    a.deleted = False
                    update_objs.append(a)
                elif action == "delete":
                    a.active = False
                    a.deleted = True
                    update_objs.append(a)
                    for creative in a.creatives:
                        creative.deleted = True
                        update_objs.append(creative)

        if update_objs:
            AdGroupQueryManager.put(update_objs)

        return HttpResponseRedirect(reverse('advertiser_campaign', kwargs={}))

@whitelist_login_required
def bid_pause(request,*args,**kwargs):
    return PauseAdGroupHandler()(request,*args,**kwargs)

# AJAX Creative Create/Edit
#
class AddCreativeHandler(RequestHandler):
    TEMPLATE    = 'advertiser/forms/creative_form.html'
    def get(self,base_creative_form=None,
                             text_creative_form=None,
                             image_creative_form=None,
                             text_tile_creative_form=None,
                             html_creative_form=None,
                             creative=None,
                             text_creative=None,
                             image_creative=None,
                             text_tile_creative=None,
                             html_creative=None):

        # TODO: Shouldn't I be able to just cast???                     
        if creative:
            if creative.ad_type == "text":
                text_creative = TextCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "text_icon":
                text_tile_creative = TextAndTileCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "image":
                image_creative = ImageCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "html":
                html_creative = HtmlCreativeQueryManager.get(creative.key())            

        # NOTE: creative is usually None so the default form is actually unbound                     
        base_creative_form = base_creative_form or BaseCreativeForm(instance=creative)
        text_creative_form = text_creative_form or TextCreativeForm(instance=text_creative)
        image_creative_form = image_creative_form or ImageCreativeForm(instance=image_creative)
        text_tile_creative_form = text_tile_creative_form or TextAndTileCreativeForm(instance=text_tile_creative)
        html_creative_form = html_creative_form or HtmlCreativeForm(instance=html_creative)

        return self.render(base_creative_form=base_creative_form,
                                    text_creative_form=text_creative_form,
                                    image_creative_form=image_creative_form,
                                    text_tile_creative_form=text_tile_creative_form,
                                    html_creative_form=html_creative_form)

    def render(self,template=None,**kwargs):
        template_name = template or self.TEMPLATE
        return render_to_string(self.request,template_name=template_name,data=kwargs)

    def json_response(self,json_dict):
        # if not self.request.FILES:
        return JSONResponse(json_dict)
        # else:
        #     logging.info("responding with: %s"%('<textarea>'+simplejson.dumps(json_dict)+'</textarea>'))
        #     return HttpResponse('<textarea>'+simplejson.dumps(json_dict)+'</textarea>',mimetype="text/plain")

    def post(self):
        ad_group = AdGroupQueryManager.get(self.request.POST.get('adgroup_key'))
        creative_key = self.request.POST.get('creative_key')
        if creative_key:
            creative = CreativeQueryManager.get(creative_key)
        else:
            creative = None

        text_creative = None
        image_creative = None
        text_tile_creative = None
        html_creative = None

        # TODO: Shouldn't I be able to just cast???                     
        if creative:
            if creative.ad_type == "text":
                text_creative = TextCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "text_icon":
                text_tile_creative = TextAndTileCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "image":
                image_creative = ImageCreativeQueryManager.get(creative.key())
            elif creative.ad_type == "html":
                html_creative = HtmlCreativeQueryManager.get(creative.key())            


        base_creative_form = BaseCreativeForm(data=self.request.POST,instance=creative)
        text_creative_form = TextCreativeForm(data=self.request.POST,instance=text_creative)
        image_creative_form = ImageCreativeForm(data=self.request.POST,files=self.request.FILES,instance=image_creative)
        text_tile_creative_form = TextAndTileCreativeForm(data=self.request.POST,files=self.request.FILES,instance=text_tile_creative)
        html_creative_form = HtmlCreativeForm(data=self.request.POST,instance=html_creative)

        jsonDict = {'success':False,'html':None}
        if base_creative_form.is_valid():
            base_creative = base_creative_form.save(commit=False)
            ad_type = base_creative.ad_type
            if ad_type == "text":
                creative_form = text_creative_form
            elif ad_type == "text_icon":
                creative_form = text_tile_creative_form
            elif ad_type == "image":
                creative_form = image_creative_form
            elif ad_type == "html":
                creative_form = html_creative_form

            if creative_form.is_valid():
                creative = creative_form.save(commit=False)
                creative.ad_group = ad_group
                creative.account = self.account
                CreativeQueryManager.put(creative)

                jsonDict.update(success=True)
                return self.json_response(jsonDict)

        new_html = self.get(base_creative_form,text_creative_form,image_creative_form,\
                                                text_tile_creative_form,html_creative_form)
        jsonDict.update(success=False,html=new_html)
        return self.json_response(jsonDict)


@whitelist_login_required
def creative_create(request,*args,**kwargs):
    return AddCreativeHandler()(request,*args,**kwargs)    

class DisplayCreativeHandler(RequestHandler):
    def get(self, creative_key):
        c = CreativeQueryManager.get(creative_key)
        if c and c.ad_type == "image" and c.image:
            return HttpResponse(c.image,content_type='image/png')
        if c and c.ad_type == "text_icon":
            if c.image:
                c.icon_url = "data:image/png;base64,%s" % binascii.b2a_base64(c.image)
            return render_to_response(self.request, 'advertiser/text_tile.html', {'c':c})
            #return HttpResponse(c.image,content_type='image/png')
        if c and c.ad_type == "html":
            return HttpResponse("<html><body style='margin:0px;'>"+c.html_data+"</body></html");
        return HttpResponse('NOOOOOOOOOOOO IMAGE')

class CreativeImageHandler(RequestHandler):
    def get(self,creative_key):
        c = CreativeQueryManager.get(creative_key)
        if c and c.image:
            return HttpResponse(c.image,content_type='image/png')
        raise Http404

def creative_image(request,*args,**kwargs):
    return DisplayCreativeHandler()(request,*args,**kwargs)

def creative_html(request,*args,**kwargs):
    return DisplayCreativeHandler()(request,*args,**kwargs)

class CreativeManagementHandler(RequestHandler):
    def post(self):
        adgroup_key = self.request.POST.get('adgroup_key')
        keys = self.request.POST.getlist('key')
        action = self.request.POST.get('action','pause')
        update_objs = []
        # TODO: bulk get before for loop
        for creative_key in keys:
            c = CreativeQueryManager.get(creative_key)
            if c != None and c.ad_group.campaign.u == self.account.user: # TODO: clean up dereferences
                if action == "pause":
                    c.deleted = False
                    c.active = False
                    update_objs.append(c)
                elif action == "resume":
                    c.deleted = False
                    c.active = True
                    update_objs.append(c)
                elif action == "delete":
                    c.deleted = True
                    c.active = False
                    update_objs.append(c)

        if update_objs:
            # db.put(update_objs)
            CreativeQueryManager.put(update_objs)

        return HttpResponseRedirect(reverse('advertiser_adgroup_show',kwargs={'adgroup_key':adgroup_key}))

@whitelist_login_required    
def creative_manage(request,*args,**kwargs):
    return CreativeManagementHandler()(request,*args,**kwargs)


class AdServerTestHandler(RequestHandler):
    def get(self):
        devices = [('iphone','iPhone'),('ipad','iPad'),('nexus_s','Nexus S')]
        device_to_user_agent = {
            'iphone': 'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_0 like Mac OS X; %s) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8A293 Safari/6531.22.7',
            'ipad': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; %s) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10',
            'nexus_s': 'Mozilla/5.0 (Linux; U; Android 0.5; %s) AppleWebKit/522+ (KHTML, like Gecko) Safari/419.3',
            'chrome': 'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.13 (KHTML, like Gecko) Chrome/0.A.B.C Safari/525.13',
        }
        country_to_locale_ip = {
            'US': ('en-US', '204.28.127.10')      ,
            'FR': ('fr-FR', '96.20.81.147')       ,
            'HR': ('hr-HR', '93.138.74.115')      ,
            'DE': ('de-DE', '212.183.113.32')     ,
            'DA': ('dk-DA', '62.107.177.124')     ,
            'FI': ('fi-FI', '91.152.79.118')      ,
            'JA': ('jp-JA', '110.163.227.87')     ,
            'HD': ('us-HD', '59.181.77.74')       ,
            'HE': ('il-HE', '99.8.113.207')       ,
            'RU': ('ru-RU', '83.149.3.32')        ,
            'NL': ('nl-NL', '77.251.143.68')      ,
            'PT': ('br-PT', '189.104.89.115')     ,
            'NB': ('no-NB', '88.89.244.197')      ,
            'TR': ('tr-TR', '78.180.93.4')        ,
            'NE': ('go-NE', '0.1.0.2')            ,
            'TH': ('th-TH', '24.52.71.42')        ,
            'RO': ('ro-RO', '85.186.180.111')     ,
            'IS': ('is-IS', '194.144.110.171')    ,
            'PL': ('pl-PL', '193.34.3.100')       ,
            'EL': ('gr-EL', '62.38.244.73')       ,
            'EN': ('us-EN', '174.255.120.125')    ,
            'ZH': ('tw-ZH', '124.190.51.251')     ,
            'MS': ('my-MS', '120.141.166.6')      ,
            'CA': ('es-CA', '95.17.76.100')       ,
            'IT': ('it-IT', '151.56.174.44')      ,
            'AR': ('sa-AR', '188.55.13.170')      ,
            'IN': ('id-IN', '114.57.226.18')      ,
            'CS': ('cz-CS', '90.180.148.68')      ,
            'HU': ('hu-HU', '85.66.221.12')       ,
            'ID': ('id-ID', '180.214.232.8')      ,
            'ES': ('ec-ES', '190.10.214.187')     ,
            'KO': ('kr-KO', '112.170.242.147')    ,
            'SV': ('se-SV', '90.225.96.11')       ,
            'SK': ('sk-SK', '213.151.218.130')    ,
            'UK': ('ua-UK', '92.244.103.199')     ,
            'SL': ('si-SL', '93.103.136.7')       ,
        }
        
        adunits = AdUnitQueryManager.get_adunits(account=self.account)
        
        return render_to_response(self.request,
                                  'advertiser/adserver_test.html',
                                  {'adunits': adunits,
                                   'devices': devices,
                                   'countries': sorted(country_to_locale_ip.keys()),
                                   'device_to_user_agent': simplejson.dumps(device_to_user_agent),
                                   'country_to_locale_ip': simplejson.dumps(country_to_locale_ip)})

@whitelist_login_required
def adserver_test(request,*args,**kwargs):
    return AdServerTestHandler()(request,*args,**kwargs)
