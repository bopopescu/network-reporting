import logging

from google.appengine.ext import db

class Counter(db.Model):
    dimension_one = db.ReferenceProperty(collection_name="dim_one_counters") # generic reference
    dimension_two = db.ReferenceProperty(collection_name="dim_two_counters") # generic reference
    date_hour = db.DateTimeProperty() # modulo to hour
    date = db.DateTimeProperty() # modulo to day
    count_one = db.IntegerProperty(default=0) #req
    count_two = db.IntegerProperty(default=0) #imp
    count_three = db.IntegerProperty(default=0) #clk
    count_four = db.IntegerProperty(default=0) #conversions
    reqs = db.ListProperty(str,indexed=False)
    
    def __init__(self, parent=None, key_name=None, **kwargs):
        if not key_name and not kwargs.get('key',None):
            dimension_one = kwargs.get('dimension_one')
            dimension_two = kwargs.get('dimension_two')            
            dimension_one = db.Key(dimension_one) if isinstance(dimension_one,(str,unicode)) else dimension_one
            dimension_two = db.Key(dimension_two) if isinstance(dimension_two,(str,unicode)) else dimension_two
            kwargs.update(dimension_one=dimension_one,dimension_two=dimension_two)
            date_hour = kwargs.get('date_hour')
            key_name = Counter.get_key_name(dimension_one,dimension_two,date_hour)
            # logging.info("key_name: %s"%key_name)
            # logging.info("Counter Model: %s %s"%(dimension_one,dimension_two))
        return super(Counter,self).__init__(key_name=key_name,**kwargs)
        
    def __add__(self,c):
        return Counter(dimension_one=Counter.dimension_one.get_value_for_datastore(self),
                        dimension_two=Counter.dimension_two.get_value_for_datastore(self),
                        date_hour=self.date_hour,
                        count_one=self.count_one + c.count_one,
                        count_two=self.count_two + c.count_two,
                        count_three=self.count_three + c.count_three,
                        count_four=self.count_four + c.count_four,
                        reqs=self.reqs+c.reqs)
    
    @classmethod
    def get_key_name(cls,dimension_one,dimension_two,date_hour,minute=False):
        if not minute:
            return 'k:%s:%s:%s'%(date_hour.strftime('%y%m%d%H'),dimension_one or '',dimension_two or '',)
        else:    
            return 'k:%s:%s:%s'%(date_hour.strftime('%y%m%d%H%M%S'),dimension_one or '',dimension_two or '',)
        
