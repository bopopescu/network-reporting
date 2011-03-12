import datetime

from google.appengine.ext import db

from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

from publisher.models import *
from advertiser.models import *

AdUnit = Site

def rollup_test():
    # TODO: have a proper set up and tear down for this test        
    app = App(key_name='app1',name='App').put()
    
    adunit1 = AdUnit(key_name='adunit1',app_key=app).put()
    adunit2 = AdUnit(key_name='adunit2',app_key=app).put()
    
    campaign = Campaign(key_name='campaign',name='campaign').put()
    adgroup = AdGroup(key_name='adgroup',campaign=campaign).put()
    creative1 = Creative(key_name='creative1',ad_group=adgroup).put()
    creative2 = Creative(key_name='creative2',ad_group=adgroup).put()
       
    adunit_id1 = str(adunit1)
    adunit_id2 = str(adunit2)
    app_id = str(app)
    creative_id1 = str(creative1)
    creative_id2 = str(creative2)
    adgroup_id = str(adgroup)
    campaign_id = str(campaign)
    date_hour = datetime.datetime(2011,02,22,03)
    date = datetime.datetime(2011,02,22)
    
    # same app, adgroup
    account = db.Key()
    
    # stat1 = db.get('agltb3B1Yi1pbmNytgELEgpTdGF0c01vZGVsIkFrOmFnbHRiM0IxWWkxcGJtTnlJZ3NTQjBGalkyOTFiblFpRlRFeE16WXhOek13TWpVNE1URTROREl5TWpFeE5ndwwLEgpTdGF0c01vZGVsIlVrOmFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVlrYW9NREE6YWdsdGIzQjFZaTFwYm1OeUVBc1NDRU55WldGMGFYWmxHS3JzSFF3OjExMDIyMjAzDA')
    stat1 = StatsModel(publisher=adunit_id1,advertiser=creative_id1,date_hour=date_hour)
    stat1.impression_count = 69
    stat1.click_count = 41
    stat1.request_count = 90
    
    # stat2 = db.get('agltb3B1Yi1pbmNytgELEgpTdGF0c01vZGVsIkFrOmFnbHRiM0IxWWkxcGJtTnlJZ3NTQjBGalkyOTFiblFpRlRFeE16WXhOek13TWpVNE1URTROREl5TWpFeE5ndwwLEgpTdGF0c01vZGVsIlVrOmFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVlrYW9NREE6YWdsdGIzQjFZaTFwYm1OeUVBc1NDRU55WldGMGFYWmxHUHFCSEF3OjExMDIyMjAzDA')
    stat2 = StatsModel(publisher=adunit_id1,advertiser=creative_id2,date_hour=date_hour)
    stat2.impression_count = 75
    stat2.click_count = 32
    stat2.request_count = 88

    stat3 = StatsModel(publisher=adunit_id2,advertiser=creative_id1,date_hour=date_hour)
    stat3.impression_count = 64
    stat3.click_count = 42
    stat3.request_count = 76
    
    # stat2 = db.get('agltb3B1Yi1pbmNytgELEgpTdGF0c01vZGVsIkFrOmFnbHRiM0IxWWkxcGJtTnlJZ3NTQjBGalkyOTFiblFpRlRFeE16WXhOek13TWpVNE1URTROREl5TWpFeE5ndwwLEgpTdGF0c01vZGVsIlVrOmFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVlrYW9NREE6YWdsdGIzQjFZaTFwYm1OeUVBc1NDRU55WldGMGFYWmxHUHFCSEF3OjExMDIyMjAzDA')
    stat4 = StatsModel(publisher=adunit_id2,advertiser=creative_id2,date_hour=date_hour)
    stat4.impression_count = 72
    stat4.click_count = 23
    stat4.request_count = 82
    
    stat5 = StatsModel(publisher=adunit_id1, advertiser=None, date_hour=date_hour)
    stat5.request_count = 100
    
    stat6 = StatsModel(publisher=adunit_id2, advertiser=None, date_hour=date_hour)
    stat6.request_count = 120

    
    
    obj_dict = {
    #### ADUNITS ####
    # Adunit-Creative
    'k:%s:%s:%s'%(adunit_id1,creative_id1,date_hour.strftime('%y%m%d%H')):(stat1.request_count,stat1.impression_count,stat1.click_count),
    'k:%s:%s:%s'%(adunit_id1,creative_id2,date_hour.strftime('%y%m%d%H')):(stat2.request_count,stat2.impression_count,stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,creative_id1,date_hour.strftime('%y%m%d%H')):(stat3.request_count,stat3.impression_count,stat3.click_count),
    'k:%s:%s:%s'%(adunit_id2,creative_id2,date_hour.strftime('%y%m%d%H')):(stat4.request_count,stat4.impression_count,stat4.click_count),
    # Adunit-AdGroup
    'k:%s:%s:%s'%(adunit_id1,adgroup_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,adgroup_id,date_hour.strftime('%y%m%d%H')):(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),
    # Adunit-Campaign
    'k:%s:%s:%s'%(adunit_id1,campaign_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,campaign_id,date_hour.strftime('%y%m%d%H')):(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),
    # Adunit Totals
    'k:%s:%s:%s'%(adunit_id1,'',date_hour.strftime('%y%m%d%H')):(stat5.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,'',date_hour.strftime('%y%m%d%H')):(stat6.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),

    #### Apps ####
    # App-Creative
    'k:%s:%s:%s'%(app_id,creative_id1,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count),
    'k:%s:%s:%s'%(app_id,creative_id2,date_hour.strftime('%y%m%d%H')):(stat2.request_count+stat4.request_count,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count),
    # App-AdGroup
    'k:%s:%s:%s'%(app_id,adgroup_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # App-Campaign
    'k:%s:%s:%s'%(app_id,campaign_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # App-Total
    'k:%s:%s:%s'%(app_id,'',date_hour.strftime('%y%m%d%H')):(stat5.request_count+stat6.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    
    
    ### * ###
    # *-Creative
    'k:%s:%s:%s'%('',creative_id1,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count),
    'k:%s:%s:%s'%('',creative_id2,date_hour.strftime('%y%m%d%H')):(stat2.request_count+stat4.request_count,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count),
    # *-AdGroup
    'k:%s:%s:%s'%('',adgroup_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # *-Campaign
    'k:%s:%s:%s'%('',campaign_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # *-*
    'k:%s:%s:%s'%('','',date_hour.strftime('%y%m%d%H')):(stat5.request_count+stat6.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    
    ####################
    ### Date Rollups ###
    ####################
    
    #### ADUNITS ####
    # Adunit-Creative
    'k:%s:%s:%s'%(adunit_id1,creative_id1,date_hour.strftime('%y%m%d')):(stat1.request_count,stat1.impression_count,stat1.click_count),
    'k:%s:%s:%s'%(adunit_id1,creative_id2,date_hour.strftime('%y%m%d')):(stat2.request_count,stat2.impression_count,stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,creative_id1,date_hour.strftime('%y%m%d')):(stat3.request_count,stat3.impression_count,stat3.click_count),
    'k:%s:%s:%s'%(adunit_id2,creative_id2,date_hour.strftime('%y%m%d')):(stat4.request_count,stat4.impression_count,stat4.click_count),
    # Adunit-AdGroup
    'k:%s:%s:%s'%(adunit_id1,adgroup_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,adgroup_id,date_hour.strftime('%y%m%d')):(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),
    # Adunit-Campaign
    'k:%s:%s:%s'%(adunit_id1,campaign_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,campaign_id,date_hour.strftime('%y%m%d')):(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),
    # Adunit Totals
    'k:%s:%s:%s'%(adunit_id1,'',date_hour.strftime('%y%m%d')):(stat5.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,'',date_hour.strftime('%y%m%d')):(stat6.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),

    #### Apps ####
    # App-Creative
    'k:%s:%s:%s'%(app_id,creative_id1,date_hour.strftime('%y%m%d')):(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count),
    'k:%s:%s:%s'%(app_id,creative_id2,date_hour.strftime('%y%m%d')):(stat2.request_count+stat4.request_count,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count),
    # App-AdGroup
    'k:%s:%s:%s'%(app_id,adgroup_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # App-Campaign
    'k:%s:%s:%s'%(app_id,campaign_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # App-Total
    'k:%s:%s:%s'%(app_id,'',date_hour.strftime('%y%m%d')):(stat5.request_count+stat6.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    


    ### * ###
    # *-Creative
    'k:%s:%s:%s'%('',creative_id1,date_hour.strftime('%y%m%d')):(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count),
    'k:%s:%s:%s'%('',creative_id2,date_hour.strftime('%y%m%d')):(stat2.request_count+stat4.request_count,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count),
    # *-AdGroup
    'k:%s:%s:%s'%('',adgroup_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # *-Campaign
    'k:%s:%s:%s'%('',campaign_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # *-*
    'k:%s:%s:%s'%('','',date_hour.strftime('%y%m%d')):(stat5.request_count+stat6.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    
    }
    
    new_stats = StatsModelQueryManager(account)._get_all_rollups([stat1,stat2,stat3,stat4,stat5,stat6])        
    
    print len(new_stats), len(obj_dict)
    assert(len(new_stats) == len(obj_dict))
    passes = True
    for stat in new_stats:
        print stat.key().name()
        print obj_dict[stat.key().name()], (stat.request_count,stat.impression_count,stat.click_count), \
              obj_dict[stat.key().name()] == (stat.request_count,stat.impression_count,stat.click_count)
        passes = passes and obj_dict[stat.key().name()] == (stat.request_count,stat.impression_count,stat.click_count)      
    return passes    
