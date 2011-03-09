import datetime

from google.appengine.ext import db
from reporting import models as r_models
from advertiser import models as a_models
from publisher import models as p_models
from account import models as ac_models

StatsModel = r_models.StatsModel
SiteStats = r_models.SiteStats

MAX_LIMIT = 10


def _append_stat(stats_dict,account,stat):
    if not account in stats_dict:
        stats_dict[account] = [stat]
    else:    
        stats_dict[account].append(stat)
        
def migrate():
    print 'getting from db: %s'%MAX_LIMIT
    site_stats = SiteStats.all().order('__key__').\
        filter('__key__ >',db.Key('agltb3B1Yi1pbmNyQgsSCVNpdGVTdGF0cyIzOmFnbHRiM0IxWWkxcGJtTnlFQXNTQ0VOeVpXRjBhWFpsR0pmNkd3dzoyMDExLTAyLTEwDA')).\
        fetch(MAX_LIMIT)
    
    cnt = 0
    while site_stats:
        cnt += 1
        if cnt > 2:
            break
        stats_dict = {}
        for site_stat in site_stats:
            if site_stat.site:
                account = site_stat.site._account
            elif site_stat.owner:
                account = site_stat.owner._account
            else:
                raise Exception("WHOA NO ACCOUNT")   
            # stat = StatsModel()    
            
            
            if site_stat.site:
                if not isinstance(site_stat.site,p_models.Site):
                    continue # bail if the site property is not actually a Site model
            if site_stat.owner:
                if not isinstance(site_stat.owner,a_models.Creative):
                    continue # bail if the owner is not a creative
                    
            if site_stat.site:
                adunit = site_stat.site
            else:
                adunit = None
                
            if site_stat.owner:
                creative = site_stat.owner
            else:
                creative = None        
                
            date = datetime.datetime(year=site_stat.date.year,
                                     month=site_stat.date.month,
                                     day=site_stat.date.day,)
            print date

            stat = StatsModel(publisher=adunit,advertiser=creative,account=account,date=date)
            stat.request_count = site_stat.request_count
            stat.impression_count = site_stat.impression_count
            stat.click_count = site_stat.click_count
            stat.conversion_count = site_stat.conversion_count
            stat.user_count = site_stat.unique_user_count
            stat.revenue = site_stat.revenue
            stat._geo_requests_json = site_stat._geo_requests_json
            stat._geo_impressions_json = site_stat._geo_impressions_json
            stat._geo_clicks_json = site_stat._geo_clicks_json
            stat._geo_revenues_json = site_stat._geo_revenues_json
            stat._geo_users_json = site_stat._geo_users_json
            
            _append_stat(stats_dict,account,stat)    
            
        # get next set of site stats
        print 'getting from db: %s'%MAX_LIMIT
        site_stats = SiteStats.all().order('__key__').\
                        filter('__key__ >',site_stats[-1].key()).\
                        fetch(MAX_LIMIT)
    print stats_dict                    
                    
    # publisher = db.ReferenceProperty(collection_name='publisher_stats')
    # advertiser = db.ReferenceProperty(collection_name='advertiser_stats')
    # account = db.ReferenceProperty(Account,collection_name='account_stats')
    # 
    # date = db.DateTimeProperty() # modulo to hour or day
    # 
    # request_count = db.IntegerProperty(default=0)
    # impression_count = db.IntegerProperty(default=0)
    # click_count = db.IntegerProperty(default=0)
    # conversion_count = db.IntegerProperty(default=0)
    # user_count = db.IntegerProperty(default=0)
    # 
    # # List of requests, useful for debugging
    # reqs = db.ListProperty(str,indexed=False)
    # 
    # # total revenue (cost)
    # revenue = db.FloatProperty(default=float(0))
    # 
    # # geo information
    # _geo_requests_json = db.StringProperty()
    # _geo_impressions_json = db.StringProperty()
    # _geo_clicks_json = db.StringProperty()
    # _geo_revenues_json = db.StringProperty()
    # _geo_users_json = db.StringProperty()
    # 
    # 
    # 
    # site = db.ReferenceProperty(Site)
    # owner = db.ReferenceProperty()
    # date = db.DateProperty()
    # request_count = db.IntegerProperty(default=0)
    # impression_count = db.IntegerProperty(default=0)
    # click_count = db.IntegerProperty(default=0)
    # unique_user_count = db.IntegerProperty(default=0)
    # revenue = db.FloatProperty(default=float(0))
    # conversion_count = db.IntegerProperty()
    # _geo_requests_json = db.TextProperty()
    # _geo_impressions_json = db.TextProperty()
    # _geo_clicks_json = db.TextProperty()
    # _geo_revenues_json = db.TextProperty()
    # _geo_users_json = db.TextProperty()
    
def attach_account(campaigns=False,adgroups=False,creatives=False):
    if campaigns:
        updates = []
        campaigns = a_models.Campaign.all().fetch(300)
        print len(campaigns)
        for c in campaigns:
            if not c.account:
                c.account = ac_models.Account.current_account(user=c.u)
                updates.append(c)
                print c.u
        db.put(updates)
    if adgroups:
        updates = []
        adgroups = a_models.AdGroup.all().fetch(300)
        print len(adgroups)
        for a in adgroups:
            if not a.account:
                a.account = a.campaign.account
                if not a.account: print 'still no account'
                updates.append(a)
        db.put(updates)        
    if creatives:    
        updates = []
        creatives = a_models.Creative.all().fetch(300)
        print len(creatives)
        cnt = 0
        for c in creatives:
            cnt += 1
            print cnt, 'of', len(creatives)
            if not c.account:
                print 'attaching account'
                c.account = c.ad_group.account
                if not c.account: print 'still no account'
                updates.append(c)
        print "putting %s in db"%len(updates)        
        db.put(updates)        
