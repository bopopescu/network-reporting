from google.appengine.ext import db

class AdminPage(db.Model):
    html = db.TextProperty()
    today_requests = db.IntegerProperty()
    loading = db.BooleanProperty(default=False)
    generated = db.DateTimeProperty(auto_now_add=True)
    
    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key',None):
            offline = kwargs.get("offline",False)
            if offline:
                key_name = "offline"
            else:
                key_name = "realtime"    
        return super(AdminPage,self).__init__(parent=parent,
                                              key_name=key_name,
                                              **kwargs)
    # type is 'offline' or 'realtime'
    @classmethod
    def get_by_stats_source(cls,offline=False):
        if offline:
            key_name = "offline"
        else:
            key_name = "realtime"    
        return cls.get_by_key_name(key_name)