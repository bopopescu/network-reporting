from google.appengine.ext import db

class AdminPage(db.Model):
    html = db.TextProperty()
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
  