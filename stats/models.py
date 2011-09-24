import mongoengine as mdb
from utils.mongo_fields import YearMonthField
from datetime import date

class Counts(mdb.EmbeddedDocument):
    """
    Count class is used to store day_counts as well as hour_counts
    If this class definition is changed, it is necessary to update
    StatsModelQueryManager._count_fields accordingly
    """
    rev = mdb.FloatField(default=0.0)
    req = mdb.IntField(default=0)
    imp = mdb.IntField(default=0)
    click = mdb.IntField(default=0)
    conv = mdb.IntField(default=0)
    att = mdb.IntField(default=0)

class StatsModel(mdb.Document):
    _id = mdb.StringField(primary_key=True)
    pub_id = mdb.StringField()
    adv_id = mdb.StringField()
    dt = YearMonthField(required=True)
    
    # key is day of month
    day_counts = mdb.MapField(field=mdb.EmbeddedDocumentField(Counts))
    # key is "day:hour"
    hour_counts = mdb.MapField(field=mdb.EmbeddedDocumentField(Counts))
    
    meta = {
        'indexes' : ['pub_id', 'adv_id']
        }

    def __init__(self, *args, **kwargs):
        #TODO: clean up a bit?
        if isinstance(kwargs['dt'], date):
            kwargs['dt'] = "%s-%02d" % (kwargs['dt'].year, kwargs['dt'].month)
        dt = kwargs['dt']
        pub_id = kwargs.get('pub_id','*')
        adv_id = kwargs.get('adv_id','*')
        kwargs['_id'] = self.get_primary_key(dt, pub_id, adv_id)
        super(StatsModel, self).__init__(*args, **kwargs)

    @classmethod
    def get_primary_key(cls, dt, pub_id, adv_id):
        return "%s:%s:%s" % (dt, pub_id, adv_id)
