import mongoengine as mdb
from utils.mongo_fields import YearMonthField
from datetime import date


class Counts(mdb.EmbeddedDocument):
    day = mdb.IntField(min_value=1, max_value=1000)
    
    rev = mdb.IntField(default=0)
    req = mdb.IntField(default=0)
    imp = mdb.IntField(default=0)
    click = mdb.IntField(default=0)
    conv = mdb.IntField(default=0)
    att = mdb.IntField(default=0)

    # uniq user counts
#     user_count = mdb.IntField(default=0)
#     req_user_count = mdb.IntField(default=0)
#     imp_user_count = mdb.IntField(default=0)
#     click_user_count = mdb.IntField(default=0)
#     att_user_count = mdb.IntField(default=0)

class HourCounts(Counts):
    hour = mdb.IntField(min_value=0, max_value=1000)
    
class StatsModel(mdb.Document):
    _id = mdb.StringField(primary_key=True)
    pub_id = mdb.StringField()
    adv_id = mdb.StringField()
    dt = YearMonthField(required=True)
    day_counts = mdb.ListField(mdb.EmbeddedDocumentField(Counts))
    # wanted to have hour counts nested in day_counts but mongoengine
    # seems to have trouble dealing with nested embedded doc lists
    hour_counts = mdb.ListField(mdb.EmbeddedDocumentField(HourCounts))

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
                        
                             
