from google.appengine.ext import db
from google.appengine.api import users

from datetime import datetime

from account.models import Account

class Report(db.Model):
    name = db.StringProperty()
    status = db.StringProperty(choices=['created', 'pending','done'], default='created')
    deleted = db.BooleanProperty(default=False)
    saved = db.BooleanProperty(default=False)

    account = db.ReferenceProperty(Account, collection_name='reports')

    created_at = db.DateTimeProperty(auto_now_add=True)
    last_viewed = db.DateTimeProperty()

    # defines the Report
    d1 = db.StringProperty(required=True) 
    d2 = db.StringProperty() 
    d3 = db.StringProperty() 
    start = db.DateProperty(required=True)
    end = db.DateProperty(required=True)

    #the actual report
    data = db.TextProperty()

    # maybe useful for internal analytics//informing users
    completed_at = db.DateTimeProperty()


#class ScheduledReport

