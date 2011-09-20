from mongoengine import StringField
from datetime import date

class YearMonthField(StringField):
    pass
#     def validate(self, value):
#         assert isinstance(value, date)
        
#     def to_python(self, value):
#         dt = value.split('-')
#         dt_obj = date(year=int(dt[0]), month=int(dt[1]), day=1)
#         print "dt!!" + str(value)
#         return "%s-%s" % (dt_obj.year, dt_obj.month)
    
#     def to_mongo(self, value):
#         print "to mongo"
#         return "%s-%s" % (value.year, value.month)
    
#     def prepare_query_value(self, op, value):
#         return "%s-%s" % (value.year, value.month)
