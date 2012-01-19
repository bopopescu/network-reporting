from appengine_django import InstallAppengineHelperForDjango
InstallAppengineHelperForDjango()


import string
import datetime

from advertiser.models import *
from publisher.models import *
from account.models import *
from registration.models import *
from google.appengine.ext import db
from google.appengine import api
from google.appengine.ext import blobstore

#######
# Random Value Generators 
#######

rand_alph = string.ascii_lowercase + string.digits 
RAND_STRING_SIZE = 6
RAND_NUM_MAX = 1000

MIN_DATE_YEAR = 2011
MAX_DATE_YEAR = 2012
MAX_DATE_DAY = 28 #hack to make sure a day is valid for any month

random_functions = {}

random_functions[db.StringProperty] = lambda : "".join([rand_alph[random.randint(0,len(rand_alph)-1)] for p in range(RAND_STRING_SIZE)])
random_functions[db.ByteString] = random_functions[db.StringProperty]
random_functions[db.TextProperty] = lambda: db.Text(random_functions[db.StringProperty]())
random_functions[db.CategoryProperty] = lambda : db.Text(random_functions[db.StringProperty]())


random_functions[db.BooleanProperty] = lambda: [True,False][random.randint(0,1)]
random_functions[db.IntegerProperty] = lambda: random.randint(0,RAND_NUM_MAX)
random_functions[db.FloatProperty] = lambda: float(random.randint(0,RAND_NUM_MAX))

random_functions[db.DateTimeProperty] = lambda : datetime.datetime(random.randint(MIN_DATE_YEAR,MAX_DATE_YEAR),
                                                                   random.randint(1,12),
                                                                   random.randint(1,MAX_DATE_DAY))
random_functions[db.DateProperty] = lambda : datetime.date(random.randint(MIN_DATE_YEAR,MAX_DATE_YEAR),
                                                                   random.randint(1,12),
                                                                   random.randint(1,MAX_DATE_DAY))
random_functions[db.TimeProperty] = random_functions[db.DateTimeProperty]

random_functions[db.ReferenceProperty] = lambda model=Campaign: get_random_model(model)
random_functions[db.SelfReferenceProperty] = random_functions[db.ReferenceProperty]

random_functions[db.GeoPtProperty] = lambda : db.GeoPt(random.random()*90,(random.random()*2-1)*180)
random_functions[db.RatingProperty] = lambda : db.Rating(random.randint(0,100))

# not implemented yet
random_functions[blobstore.BlobReferenceProperty] = lambda : None
random_functions[db.BlobProperty] = lambda : db.Blob()
random_functions[db.LinkProperty] = lambda: db.Link("http://mopub.com")
random_functions[db.EmailProperty] = lambda: db.Email("mopub@mopub.com")
random_functions[db.IMProperty] = lambda : db.IM("","")
random_functions[db.PhoneNumberProperty] = lambda : db.PhoneNumber("1 (999) 999-9999")
random_functions[db.PostalAddressProperty] = lambda : db.PostalAddress("Mopub, MP, 00000")
random_functions[db.UserProperty] = lambda : get_random_model(Account) if get_random_model(Account) else None
random_functions[db.StringListProperty] = lambda : []
random_functions[db.ListProperty] = lambda : []

def get_random_model(Model):
    total_records = Model.all().count()
    if total_records:
        return Model.get_by_id(random.randint(1,total_records))
    return None


def generate_random_instance(cls):
    data = {}
    for prop_name,value in cls.properties().items():
        if issubclass(value.__class__,db.ReferenceProperty):
            rand_val = get_random_model(value.reference_class)
        elif hasattr(value,"choices") and value.choices:
            rand_val = value.choices[random.randint(0,len(value.choices)-1)]
        else:
            rand_val = random_functions[value.__class__]()
            rand_val = rand_val if rand_val else value.default
            data[prop_name] = rand_val
    return cls(**data)


if __name__=="__main__":
#     for db_type,rand_func in random_functions.items():
#         print "%s - %s" % (db_type,rand_func())
    models = [NetworkConfig,MarketPlaceConfig,Account,PaymentInfo,PaymentRecord,
              App,AdUnit,Campaign,AdGroup]

    for model in models:
        print generate_random_instance(model)



