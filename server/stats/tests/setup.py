# TESTING INSTRUCTIONS
# $ ./manage.py shell/
#  > import stats.tests.setup as s
#  > s.setup_models()
#  > exit()
# 
# $ ./manage.py runserver
#  
# (Then follow instructions in laoder.py)

from google.appengine.ext import db

from account.models import Account, User
from publisher.models import App, AdUnit
from advertiser.models import Campaign, AdGroup, HtmlCreative
from reporting.models import StatsModel

# set up a lot of cross products within an account
def setup_models():
    # delete all stats
    db.delete(StatsModel.all())
    
    # create 1 account, app
    account = Account.get_by_id(1)
    account.number_shards = 4
    account.put()
        
    app = App(key_name='app',name='app',account=account)
    app.put()
    
    # create 100 adunits
    adunits = []
    for i in xrange(100):
        adunit = AdUnit(key_name='adunit_%02d'%i,
                        app_key=app,
                        name='Banner Ad #%02d'%i,
                        format='320x50',
                        account=account)
        adunits.append(adunit)
    db.put(adunits)
    
    
    # create 1 campaign, adgroup, creative
    campaign = Campaign(key_name='campaign',
                        name='campaign',
                        campaign_type='gtee',
                        account=account)
    campaign.put()
    
    adgroup = AdGroup(key_name='adgroup',
                      account=account,
                      campaign=campaign,
                      site_keys=[a.key() for a in adunits])
    adgroup.put()
    
    creative = HtmlCreative(key_name='creative',
                            html_data='<b>hello world</b>',
                            ad_type='html',
                            ad_group=adgroup,
                            account=account)
    creative.put()                        
    

if __name__ == '__main__':
    setup()
