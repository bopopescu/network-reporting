import sys
import os
import logging
import datetime

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from google.appengine.ext import db
from nose.tools import assert_equals

import reporting.models as reporting_models
from reporting.models import StatsModel
from reporting.query_managers import StatsModelQueryManager

from publisher.models import *
from advertiser.models import *

AdUnit = Site

app = App(key_name='app1',name='App').put()

adunit1 = AdUnit(key_name='adunit1',app_key=app).put()
adunit2 = AdUnit(key_name='adunit2',app_key=app).put()

campaign = Campaign(key_name='campaign',name='campaign').put()
adgroup = AdGroup(key_name='adgroup',campaign=campaign).put()
creative1 = Creative(key_name='creative1',ad_group=adgroup).put()
creative2 = Creative(key_name='creative2',ad_group=adgroup).put()
   
country1 = "US"
country2 = "UK" 
countries = [country1,country2]  
   
adunit_id1 = str(adunit1)
adunit_id2 = str(adunit2)
app_id = str(app)
creative_id1 = str(creative1)
creative_id2 = str(creative2)
adgroup_id = str(adgroup)
campaign_id = str(campaign)
date_hour = datetime.datetime(2011,02,22,03)

logging.info('adunit1:%s'%adunit_id1)
logging.info('adunit2:%s'%adunit_id2)
logging.info('app:%s'%app_id)
logging.info('creative1:%s'%creative1)
logging.info('creative2:%s'%creative2)
logging.info('adgroup:%s'%adgroup)
logging.info('campaign:%s'%campaign)

# same app, adgroup
account = Account(key_name="account").key()

# stat1 = db.get('agltb3B1Yi1pbmNytgELEgpTdGF0c01vZGVsIkFrOmFnbHRiM0IxWWkxcGJtTnlJZ3NTQjBGalkyOTFiblFpRlRFeE16WXhOek13TWpVNE1URTROREl5TWpFeE5ndwwLEgpTdGF0c01vZGVsIlVrOmFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVlrYW9NREE6YWdsdGIzQjFZaTFwYm1OeUVBc1NDRU55WldGMGFYWmxHS3JzSFF3OjExMDIyMjAzDA')
stat1 = StatsModel(publisher=adunit_id1,advertiser=creative_id1,date_hour=date_hour,country=country1)
stat1.impression_count = 69
stat1.click_count = 41
stat1.request_count = 90

# stat2 = db.get('agltb3B1Yi1pbmNytgELEgpTdGF0c01vZGVsIkFrOmFnbHRiM0IxWWkxcGJtTnlJZ3NTQjBGalkyOTFiblFpRlRFeE16WXhOek13TWpVNE1URTROREl5TWpFeE5ndwwLEgpTdGF0c01vZGVsIlVrOmFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVlrYW9NREE6YWdsdGIzQjFZaTFwYm1OeUVBc1NDRU55WldGMGFYWmxHUHFCSEF3OjExMDIyMjAzDA')
stat2 = StatsModel(publisher=adunit_id1,advertiser=creative_id2,date_hour=date_hour,country=country2)
stat2.impression_count = 75
stat2.click_count = 32
stat2.request_count = 88

stat3 = StatsModel(publisher=adunit_id2,advertiser=creative_id1,date_hour=date_hour,country=country1)
stat3.impression_count = 64
stat3.click_count = 42
stat3.request_count = 76

# stat2 = db.get('agltb3B1Yi1pbmNytgELEgpTdGF0c01vZGVsIkFrOmFnbHRiM0IxWWkxcGJtTnlJZ3NTQjBGalkyOTFiblFpRlRFeE16WXhOek13TWpVNE1URTROREl5TWpFeE5ndwwLEgpTdGF0c01vZGVsIlVrOmFnbHRiM0IxWWkxcGJtTnlEQXNTQkZOcGRHVVlrYW9NREE6YWdsdGIzQjFZaTFwYm1OeUVBc1NDRU55WldGMGFYWmxHUHFCSEF3OjExMDIyMjAzDA')
stat4 = StatsModel(publisher=adunit_id2,advertiser=creative_id2,date_hour=date_hour,country=country1)
stat4.impression_count = 72
stat4.click_count = 23
stat4.request_count = 82

stat5 = StatsModel(publisher=adunit_id1, advertiser=None, date_hour=date_hour,country=country1)
stat5.request_count = 100

stat6 = StatsModel(publisher=adunit_id2, advertiser=None, date_hour=date_hour,country=country1)
stat6.request_count = 120


obj_dict = {
#### ADUNITS ####
# Adunit-Creative
'k:%s:%s:%s'%(adunit_id1,creative_id1,date_hour.strftime('%y%m%d%H')):(stat1.request_count,stat1.impression_count,stat1.click_count,
                                                            {country1:(stat1.request_count,stat1.impression_count,stat1.click_count)}),
'k:%s:%s:%s'%(adunit_id1,creative_id2,date_hour.strftime('%y%m%d%H')):(stat2.request_count,stat2.impression_count,stat2.click_count,
                                                            {country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,creative_id1,date_hour.strftime('%y%m%d%H')):(stat3.request_count,stat3.impression_count,stat3.click_count,
                                                            {country1:(stat3.request_count,stat3.impression_count,stat3.click_count)}),
'k:%s:%s:%s'%(adunit_id2,creative_id2,date_hour.strftime('%y%m%d%H')):(stat4.request_count,stat4.impression_count,stat4.click_count,
                                                            {country1:(stat4.request_count,stat4.impression_count,stat4.click_count)}),
# Adunit-AdGroup
'k:%s:%s:%s'%(adunit_id1,adgroup_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count,
                                                          {country1:(stat1.request_count,stat1.impression_count,stat1.click_count),country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,adgroup_id,date_hour.strftime('%y%m%d%H')):(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count,
                                                          {country1:(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count)}),
# Adunit-Campaign
'k:%s:%s:%s'%(adunit_id1,campaign_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count,
                                                           {country1:(stat1.request_count,stat1.impression_count,stat1.click_count),
                                                            country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,campaign_id,date_hour.strftime('%y%m%d%H')):(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count,
                                                           {country1:(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count)}),
# Adunit Totals
'k:%s:%s:%s'%(adunit_id1,'',date_hour.strftime('%y%m%d%H')):(stat5.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count,
                                                  {country1:(stat5.request_count,stat1.impression_count,stat1.click_count),
                                                   country2:(0,                  stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,'',date_hour.strftime('%y%m%d%H')):(stat6.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count,
                                                  {country1:(stat6.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count)}),

#### Apps ####
# App-Creative
'k:%s:%s:%s'%(app_id,creative_id1,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count,
                                                        {country1:(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count)}),
'k:%s:%s:%s'%(app_id,creative_id2,date_hour.strftime('%y%m%d%H')):(stat2.request_count+stat4.request_count,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count,
                                                        {country2:(stat2.request_count,stat2.impression_count,stat2.click_count),
                                                         country1:(stat4.request_count,stat4.impression_count,stat4.click_count)}),
# App-AdGroup
'k:%s:%s:%s'%(app_id,adgroup_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                                      {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                       country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),    
# App-Campaign
'k:%s:%s:%s'%(app_id,campaign_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                                       {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                        country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),    

# App-Total
'k:%s:%s:%s'%(app_id,'',date_hour.strftime('%y%m%d%H')):(stat5.request_count+stat6.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                              {country1:(stat5.request_count+stat6.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                               country2:(0,stat2.impression_count,stat2.click_count)}),    


### * ###
# *-Creative
'k:%s:%s:%s'%('',creative_id1,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count,
                                                    {country1:(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count)}),
'k:%s:%s:%s'%('',creative_id2,date_hour.strftime('%y%m%d%H')):(stat2.request_count+stat4.request_count,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count,
                                                    {country1:(stat4.request_count,stat4.impression_count,stat4.click_count),
                                                     country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
# *-AdGroup
'k:%s:%s:%s'%('',adgroup_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,    
                                                  {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                   country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
# *-Campaign
'k:%s:%s:%s'%('',campaign_id,date_hour.strftime('%y%m%d%H')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,    
                                                   {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                    country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
   
# *-*
'k:%s:%s:%s'%('','',date_hour.strftime('%y%m%d%H')):(stat5.request_count+stat6.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                          {country1:(stat5.request_count+stat6.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                           country2:(0,stat2.impression_count,stat2.click_count)}),    

####################
### Date Rollups ###
####################

### Date ###

#### ADUNITS ####
# Adunit-Creative
'k:%s:%s:%s'%(adunit_id1,creative_id1,date_hour.strftime('%y%m%d')):(stat1.request_count,stat1.impression_count,stat1.click_count,
                                                            {country1:(stat1.request_count,stat1.impression_count,stat1.click_count)}),
'k:%s:%s:%s'%(adunit_id1,creative_id2,date_hour.strftime('%y%m%d')):(stat2.request_count,stat2.impression_count,stat2.click_count,
                                                            {country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,creative_id1,date_hour.strftime('%y%m%d')):(stat3.request_count,stat3.impression_count,stat3.click_count,
                                                            {country1:(stat3.request_count,stat3.impression_count,stat3.click_count)}),
'k:%s:%s:%s'%(adunit_id2,creative_id2,date_hour.strftime('%y%m%d')):(stat4.request_count,stat4.impression_count,stat4.click_count,
                                                            {country1:(stat4.request_count,stat4.impression_count,stat4.click_count)}),
# Adunit-AdGroup
'k:%s:%s:%s'%(adunit_id1,adgroup_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count,
                                                          {country1:(stat1.request_count,stat1.impression_count,stat1.click_count),country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,adgroup_id,date_hour.strftime('%y%m%d')):(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count,
                                                          {country1:(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count)}),
# Adunit-Campaign
'k:%s:%s:%s'%(adunit_id1,campaign_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count,
                                                           {country1:(stat1.request_count,stat1.impression_count,stat1.click_count),
                                                            country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,campaign_id,date_hour.strftime('%y%m%d')):(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count,
                                                           {country1:(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count)}),
# Adunit Totals
'k:%s:%s:%s'%(adunit_id1,'',date_hour.strftime('%y%m%d')):(stat5.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count,
                                                 {country1:(stat5.request_count,stat1.impression_count,stat1.click_count),
                                                  country2:(0,                  stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,'',date_hour.strftime('%y%m%d')):(stat6.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count,
                                                  {country1:(stat6.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count)}),

#### Apps ####
# App-Creative
'k:%s:%s:%s'%(app_id,creative_id1,date_hour.strftime('%y%m%d')):(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count,
                                                        {country1:(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count)}),
'k:%s:%s:%s'%(app_id,creative_id2,date_hour.strftime('%y%m%d')):(stat2.request_count+stat4.request_count,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count,
                                                        {country2:(stat2.request_count,stat2.impression_count,stat2.click_count),
                                                         country1:(stat4.request_count,stat4.impression_count,stat4.click_count)}),
# App-AdGroup
'k:%s:%s:%s'%(app_id,adgroup_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                                      {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                       country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),    
# App-Campaign
'k:%s:%s:%s'%(app_id,campaign_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                                       {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                        country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),    

# App-Total
'k:%s:%s:%s'%(app_id,'',date_hour.strftime('%y%m%d')):(stat5.request_count+stat6.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                              {country1:(stat5.request_count+stat6.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                               country2:(0,stat2.impression_count,stat2.click_count)}),    


### * ###
# *-Creative
'k:%s:%s:%s'%('',creative_id1,date_hour.strftime('%y%m%d')):(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count,
                                                    {country1:(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count)}),
'k:%s:%s:%s'%('',creative_id2,date_hour.strftime('%y%m%d')):(stat2.request_count+stat4.request_count,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count,
                                                    {country1:(stat4.request_count,stat4.impression_count,stat4.click_count),
                                                     country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
# *-AdGroup
'k:%s:%s:%s'%('',adgroup_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,    
                                                  {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                   country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
# *-Campaign
'k:%s:%s:%s'%('',campaign_id,date_hour.strftime('%y%m%d')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,    
                                                   {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                    country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
   
# *-*
'k:%s:%s:%s'%('','',date_hour.strftime('%y%m%d')):(stat5.request_count+stat6.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                          {country1:(stat5.request_count+stat6.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                           country2:(0,stat2.impression_count,stat2.click_count)}),    

### Month ###

#### ADUNITS ####
# Adunit-Creative
'k:%s:%s:%s'%(adunit_id1,creative_id1,date_hour.strftime('%y%m')):(stat1.request_count,stat1.impression_count,stat1.click_count,
                                                            {country1:(stat1.request_count,stat1.impression_count,stat1.click_count)}),
'k:%s:%s:%s'%(adunit_id1,creative_id2,date_hour.strftime('%y%m')):(stat2.request_count,stat2.impression_count,stat2.click_count,
                                                            {country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,creative_id1,date_hour.strftime('%y%m')):(stat3.request_count,stat3.impression_count,stat3.click_count,
                                                            {country1:(stat3.request_count,stat3.impression_count,stat3.click_count)}),
'k:%s:%s:%s'%(adunit_id2,creative_id2,date_hour.strftime('%y%m')):(stat4.request_count,stat4.impression_count,stat4.click_count,
                                                            {country1:(stat4.request_count,stat4.impression_count,stat4.click_count)}),
# Adunit-AdGroup
'k:%s:%s:%s'%(adunit_id1,adgroup_id,date_hour.strftime('%y%m')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count,
                                                          {country1:(stat1.request_count,stat1.impression_count,stat1.click_count),country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,adgroup_id,date_hour.strftime('%y%m')):(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count,
                                                          {country1:(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count)}),
# Adunit-Campaign
'k:%s:%s:%s'%(adunit_id1,campaign_id,date_hour.strftime('%y%m')):(stat1.request_count+stat2.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count,
                                                           {country1:(stat1.request_count,stat1.impression_count,stat1.click_count),
                                                            country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,campaign_id,date_hour.strftime('%y%m')):(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count,
                                                           {country1:(stat3.request_count+stat4.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count)}),
# Adunit Totals
'k:%s:%s:%s'%(adunit_id1,'',date_hour.strftime('%y%m')):(stat5.request_count,stat1.impression_count+stat2.impression_count,stat1.click_count+stat2.click_count,
                                                  {country1:(stat5.request_count,stat1.impression_count,stat1.click_count),
                                                   country2:(0,                  stat2.impression_count,stat2.click_count)}),
'k:%s:%s:%s'%(adunit_id2,'',date_hour.strftime('%y%m')):(stat6.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count,
                                                  {country1:(stat6.request_count,stat3.impression_count+stat4.impression_count,stat3.click_count+stat4.click_count)}),

#### Apps ####
# App-Creative
'k:%s:%s:%s'%(app_id,creative_id1,date_hour.strftime('%y%m')):(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count,
                                                        {country1:(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count)}),
'k:%s:%s:%s'%(app_id,creative_id2,date_hour.strftime('%y%m')):(stat2.request_count+stat4.request_count,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count,
                                                        {country2:(stat2.request_count,stat2.impression_count,stat2.click_count),
                                                         country1:(stat4.request_count,stat4.impression_count,stat4.click_count)}),
# App-AdGroup
'k:%s:%s:%s'%(app_id,adgroup_id,date_hour.strftime('%y%m')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                                      {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                       country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),    
# App-Campaign
'k:%s:%s:%s'%(app_id,campaign_id,date_hour.strftime('%y%m')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                                       {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                        country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),    

# App-Total
'k:%s:%s:%s'%(app_id,'',date_hour.strftime('%y%m')):(stat5.request_count+stat6.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                              {country1:(stat5.request_count+stat6.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                               country2:(0,stat2.impression_count,stat2.click_count)}),    


### * ###
# *-Creative
'k:%s:%s:%s'%('',creative_id1,date_hour.strftime('%y%m')):(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count,
                                                    {country1:(stat1.request_count+stat3.request_count,stat1.impression_count+stat3.impression_count,stat1.click_count+stat3.click_count)}),
'k:%s:%s:%s'%('',creative_id2,date_hour.strftime('%y%m')):(stat2.request_count+stat4.request_count,stat2.impression_count+stat4.impression_count,stat2.click_count+stat4.click_count,
                                                    {country1:(stat4.request_count,stat4.impression_count,stat4.click_count),
                                                     country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
# *-AdGroup
'k:%s:%s:%s'%('',adgroup_id,date_hour.strftime('%y%m')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,    
                                                  {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                   country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
# *-Campaign
'k:%s:%s:%s'%('',campaign_id,date_hour.strftime('%y%m')):(stat1.request_count+stat2.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,    
                                                   {country1:(stat1.request_count+stat3.request_count+stat4.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                                    country2:(stat2.request_count,stat2.impression_count,stat2.click_count)}),
   
# *-*
'k:%s:%s:%s'%('','',date_hour.strftime('%y%m')):(stat5.request_count+stat6.request_count,stat1.impression_count+stat2.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat2.click_count+stat3.click_count+stat4.click_count,
                                          {country1:(stat5.request_count+stat6.request_count,stat1.impression_count+stat3.impression_count+stat4.impression_count,stat1.click_count+stat3.click_count+stat4.click_count),
                                           country2:(0,stat2.impression_count,stat2.click_count)}),    
}



def rollup_mptest():  
    # make sure we start this unit test with clean slate
    db.delete(StatsModel.all())
    assert_equals(StatsModel.all().count(), 0)
    
    assert_equals(App.all().count(), 1)
    assert_equals(Campaign.all().count(), 1)
    assert_equals(AdGroup.all().count(), 1)
    assert_equals(AdUnit.all().count(), 2)
    assert_equals(Creative.all().count(), 2)
    
    new_stats = StatsModelQueryManager(account).put_stats([stat1,stat2,stat3,stat4,stat5,stat6])        
    assert_equals(len(obj_dict), 60)        
    assert_equals(len(new_stats), 61) # one extra one for the account
    
    for stat in new_stats:
        obj = StatsModel.get(stat)
        key_name = obj.key().name()
        if len(key_name.split(':')) == 2: continue # skip the account 
        
        # assert that request, impression and click are the same
        assert_equals(obj_dict[key_name][:3], (obj.request_count,obj.impression_count,obj.click_count))

        # assert that the geo counts are correct as well
        for country in countries:
            if country in obj_dict[key_name][3]:
                print key_name, country
                assert_equals(obj_dict[key_name][3][country], (obj.get_geo(country,reporting_models.GEO_REQUEST_COUNT),
                                                               obj.get_geo(country,reporting_models.GEO_IMPRESSION_COUNT),
                                                               obj.get_geo(country,reporting_models.GEO_CLICK_COUNT),
                                                              ))

    # remove all StatsModels for next unit test
    db.delete(StatsModel.all())
    assert_equals(StatsModel.all().count(), 0)
