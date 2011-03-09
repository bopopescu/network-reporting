from google.appengine.ext import db
from advertiser.models import AdGroup, Creative

def migrate():
    for adgroup in AdGroup.all():
        if adgroup.network_type and not adgroup.net_creative:
            print adgroup.network_type
            creatives = adgroup.creatives
            if creatives:
                db.delete(creatives)
            cret = adgroup.default_creative()
            cret.account = adgroup.account
            print "putting creative"
            cret.put()
            adgroup.net_creative = cret 
            print "puttin adgroup"
            adgroup.put()
