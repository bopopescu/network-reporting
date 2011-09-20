import mongoengine as mdb
from utils.mongo_fields import YearMonthField
from datetime import date

class StatsModel(mdb.Document):
    _id = mdb.StringField(primary_key=True)
    pub_id = mdb.StringField()
    adv_id = mdb.StringField()
    dt = YearMonthField(required=True)

    country = mdb.StringField() # two letter country code
    
    req_count = mdb.IntField(default=0)
    imp_count = mdb.IntField(default=0)
    click_count = mdb.IntField(default=0)
    conv_count = mdb.IntField(default=0)

    # uniq user counts
    user_count = mdb.IntField(default=0)
    req_user_count = mdb.IntField(default=0)
    imp_user_count = mdb.IntField(default=0)
    click_user_count = mdb.IntField(default=0)
    
    reqs = mdb.ListField(mdb.StringField())
    
    # total revenue (cost)
    rev = mdb.FloatField(default=0.0)
    
    # offline
    offline = mdb.BooleanField(default=False)
    
    # mobile device and os info
    brand_name = mdb.StringField()
    marketing_name = mdb.StringField()
    device_os = mdb.StringField()
    device_os_vers = mdb.StringField()

    def __init__(self, *args, **kwargs):
        # TODO: a bit hackish, converts passed in date to string
        if isinstance(kwargs['dt'], date):
            kwargs['dt'] = "%s-%02d" % (kwargs['dt'].year, kwargs['dt'].month)
        dt = kwargs['dt']
        pub_id = kwargs['pub_id']
        adv_id = kwargs['adv_id']
        kwargs['_id'] = self.get_primary_key(dt, pub_id, adv_id)
        super(StatsModel, self).__init__(*args, **kwargs)

    @classmethod
    def get_primary_key(cls, dt, pub_id, adv_id):
        return "%s:%s:%s" % (dt, pub_id, adv_id)
                        
                             
