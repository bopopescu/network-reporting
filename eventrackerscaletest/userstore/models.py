import logging

from google.appengine.ext import db

from django.utils import simplejson

class MobileUser(db.Model):
    udid = db.StringProperty()
    clicks = db.StringListProperty(default=[],indexed=False) # {'t':'<time>','<adunit>|<creative>':'<appid>'}
    apps = db.StringListProperty(default=[],indexed=False)
    
    
    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key',None):
            udid = kwargs.get('udid',None)
            if udid:
                key_name = self.get_key_name(udid)
        return super(MobileUser,self).__init__(key_name=key_name,**kwargs)
    
    @classmethod
    def get_key_name(cls,udid):
        return 'k:%s'%udid
    
    @classmethod    
    def get_by_udid(cls,udid):
        return cls.get_by_key_name(cls.get_key_name(udid))
        
    def add_app(self,app):
        # add if anot already there
        if not app in self.apps:
            self.apps.append(app)
        return self._conversions_for_app(app)
        
    def _conversions_for_app(self,app):
        click_dict = {}
        # go through in reverse order
        for c in self.clicks[::-1]:
            data = simplejson.loads(c)
            time = data.pop('t')
            value = data.values()[0] # there should only be one
            if value == app:
                adunit_creative = data.keys()[0] # there should only be one 
                return adunit_creative.split('|')
        return None,None        
    
    def add_click(self,adunit,creative,time,appid):
        key = '%s|%s'%(adunit,creative)
        obj = {key:appid,'t':time}
        obj_string = simplejson.dumps(obj)
        self.clicks.append(obj_string)
        # sorts in order of oldest to newest
        self.clicks.sort(cmp=lambda x,y:cmp(simplejson.loads(x)['t'],simplejson.loads(y)['t']))