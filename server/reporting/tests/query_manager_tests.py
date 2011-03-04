import datetime

from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager


def rollup_test():
    # TODO: have a proper set up and tear down for this test           
    adunit_id1 = "agltb3B1Yi1pbmNyDAsSBFNpdGUYkaoMDA"
    adunit_id2 = "agltb3B1Yi1pbmNyDAsSBFNpdGUYq-wdDA"
    app_id = "agltb3B1Yi1pbmNyCwsSA0FwcBii-wsM"
    creative_id1 = "agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGKrsHQw"
    creative_id2 = "agltb3B1Yi1pbmNyEAsSCENyZWF0aXZlGPqBHAw"
    adgroup_id = "agltb3B1Yi1pbmNyDwsSB0FkR3JvdXAY840LDA"
    campaign_id = "agltb3B1Yi1pbmNyEAsSCENhbXBhaWduGPmxDAw"
    date_hour = datetime.datetime(2011,02,22,03)
    date = datetime.datetime(2011,02,22)
    
    # same app, adgroup
    account = db.Key()
    
    # stat1 = db.get('agltb3B1Yi1pbmNytgELEgpTdGF0c01vZGVsIkFrOmFnbHRiM0IxWWkxcGJtTnlJZ3NTQjBGalkyOTFiblFpRlRFeE16WXhOek13TWpVNE1URTROREl5TWpFeE5ndwwLEgpTdGF0c01vZGVsIlVrOmFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVlrYW9NREE6YWdsdGIzQjFZaTFwYm1OeUVBc1NDRU55WldGMGFYWmxHS3JzSFF3OjExMDIyMjAzDA')
    stat1 = StatsModel(publisher=adunit_id1,advertiser=creative_id1,date_hour=date_hour)
    stat1.impression_count = 69
    stat1.click_count = 41
    # stat2 = db.get('agltb3B1Yi1pbmNytgELEgpTdGF0c01vZGVsIkFrOmFnbHRiM0IxWWkxcGJtTnlJZ3NTQjBGalkyOTFiblFpRlRFeE16WXhOek13TWpVNE1URTROREl5TWpFeE5ndwwLEgpTdGF0c01vZGVsIlVrOmFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVlrYW9NREE6YWdsdGIzQjFZaTFwYm1OeUVBc1NDRU55WldGMGFYWmxHUHFCSEF3OjExMDIyMjAzDA')
    stat2 = StatsModel(publisher=adunit_id1,advertiser=creative_id2,date_hour=date_hour)
    stat2.impression_count = 75
    stat2.click_count = 32

    stat3 = StatsModel(publisher=adunit_id2,advertiser=creative_id1,date_hour=date_hour)
    stat3.impression_count = 64
    stat3.click_count = 42
    # stat2 = db.get('agltb3B1Yi1pbmNytgELEgpTdGF0c01vZGVsIkFrOmFnbHRiM0IxWWkxcGJtTnlJZ3NTQjBGalkyOTFiblFpRlRFeE16WXhOek13TWpVNE1URTROREl5TWpFeE5ndwwLEgpTdGF0c01vZGVsIlVrOmFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVlrYW9NREE6YWdsdGIzQjFZaTFwYm1OeUVBc1NDRU55WldGMGFYWmxHUHFCSEF3OjExMDIyMjAzDA')
    stat4 = StatsModel(publisher=adunit_id2,advertiser=creative_id2,date_hour=date_hour)
    stat4.impression_count = 72
    stat4.click_count = 23
    
    
    obj_dict = {
    #### ADUNITS ####
    # Adunit-Creative
    'k:%s:%s:%s'%(adunit_id1,creative_id1,date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count,stat1.click_count),
    'k:%s:%s:%s'%(adunit_id1,creative_id2,date_hour.strftime('%y%m%d%H')):(0,stat2.impression_count,stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,creative_id1,date_hour.strftime('%y%m%d%H')):(0,stat3.impression_count,stat3.click_count),
    'k:%s:%s:%s'%(adunit_id2,creative_id2,date_hour.strftime('%y%m%d%H')):(0,stat4.impression_count,stat4.click_count),
    # Adunit-AdGroup
    'k:%s:%s:%s'%(adunit_id1,adgroup_id,date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,adgroup_id,date_hour.strftime('%y%m%d%H')):(0,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),
    # Adunit-Campaign
    'k:%s:%s:%s'%(adunit_id1,campaign_id,date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,campaign_id,date_hour.strftime('%y%m%d%H')):(0,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),
    # Adunit Totals
    'k:%s:%s:%s'%(adunit_id1,'',date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,'',date_hour.strftime('%y%m%d%H')):(0,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),

    #### Apps ####
    # App-Creative
    'k:%s:%s:%s'%(app_id,creative_id1,date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count),
    'k:%s:%s:%s'%(app_id,creative_id2,date_hour.strftime('%y%m%d%H')):(0,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count),
    # App-AdGroup
    'k:%s:%s:%s'%(app_id,adgroup_id,date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # App-Campaign
    'k:%s:%s:%s'%(app_id,campaign_id,date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # App-Total
    'k:%s:%s:%s'%(app_id,'',date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    
    
    ### * ###
    # *-Creative
    'k:%s:%s:%s'%('',creative_id1,date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count),
    'k:%s:%s:%s'%('',creative_id2,date_hour.strftime('%y%m%d%H')):(0,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count),
    # *-AdGroup
    'k:%s:%s:%s'%('',adgroup_id,date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # *-Campaign
    'k:%s:%s:%s'%('',campaign_id,date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # *-*
    'k:%s:%s:%s'%('','',date_hour.strftime('%y%m%d%H')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    
    ####################
    ### Date Rollups ###
    ####################
    
    #### ADUNITS ####
    'k:%s:%s:%s'%(adunit_id1,creative_id1,date_hour.strftime('%y%m%d')):(0,stat1.impression_count,stat1.click_count),
    'k:%s:%s:%s'%(adunit_id1,creative_id2,date_hour.strftime('%y%m%d')):(0,stat2.impression_count,stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,creative_id1,date_hour.strftime('%y%m%d')):(0,stat3.impression_count,stat3.click_count),
    'k:%s:%s:%s'%(adunit_id2,creative_id2,date_hour.strftime('%y%m%d')):(0,stat4.impression_count,stat4.click_count),
    # Adunit-AdGroup
    'k:%s:%s:%s'%(adunit_id1,adgroup_id,date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,adgroup_id,date_hour.strftime('%y%m%d')):(0,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),
    # Adunit-Campaign
    'k:%s:%s:%s'%(adunit_id1,campaign_id,date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,campaign_id,date_hour.strftime('%y%m%d')):(0,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),
    # Adunit Totals
    'k:%s:%s:%s'%(adunit_id1,'',date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count),
    'k:%s:%s:%s'%(adunit_id2,'',date_hour.strftime('%y%m%d')):(0,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count),

    #### Apps ####
    # App-Creative
    'k:%s:%s:%s'%(app_id,creative_id1,date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count),
    'k:%s:%s:%s'%(app_id,creative_id2,date_hour.strftime('%y%m%d')):(0,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count),
    # App-AdGroup
    'k:%s:%s:%s'%(app_id,adgroup_id,date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # App-Campaign
    'k:%s:%s:%s'%(app_id,campaign_id,date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # App-Total
    'k:%s:%s:%s'%(app_id,'',date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    
    
    ### * ###
    # *-Creative
    'k:%s:%s:%s'%('',creative_id1,date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count),
    'k:%s:%s:%s'%('',creative_id2,date_hour.strftime('%y%m%d')):(0,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count),
    # *-AdGroup
    'k:%s:%s:%s'%('',adgroup_id,date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # *-Campaign
    'k:%s:%s:%s'%('',campaign_id,date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    # *-*
    'k:%s:%s:%s'%('','',date_hour.strftime('%y%m%d')):(0,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count),    
    
    }
    
    new_stats = StatsModelQueryManager(account)._get_all_rollups([stat1,stat2])        
    
    print len(new_stats), len(obj_dict)
    assert(len(new_stats) == len(obj_dict))
    passes = True
    for stat in new_stats:
        print stat.key().name()
        print obj_dict[stat.key().name()], (stat.request_count,stat.impression_count,stat.click_count), \
              obj_dict[stat.key().name()] == (stat.request_count,stat.impression_count,stat.click_count)
        passes = passes and obj_dict[stat.key().name()] == (stat.request_count,stat.impression_count,stat.click_count)      
    return passes    
