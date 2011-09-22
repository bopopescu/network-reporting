from datetime import date, datetime
from query_managers import StatsModelQueryManager
from models import StatsModel, HourCounts, Counts
from utils import mongo_connection


# import json
# fields2 = json.loads('{"request":1, "impression":2}')
# fields = json.loads('{"bar":"baz"}')
# print fields2

#StatsModelQueryManager.create_empty_results()
mongo_connection.ensure_connection()
# stats = StatsModel(dt=date(2011,3,3), pub_id='fake_pub_id', adv_id='adv_id')
# stats.save()

#hc = HourCounts()
#stats_model = StatsModel.objects().first()
StatsModel.objects().update(set__day_counts__a__req=1)
#stats_model.day_counts["a"] = hc
#stats_model.save()



# print StatsModelQueryManager.get_counts(start_date=date(2012,3,1), 
#                                         end_date=date(2012,3,25))

# vals = StatsModel.objects
# for val in vals:
#2011-09:app_id:creative_id
# StatsModelQueryManager.get_stats_within_month(pub_id="app_id",
#                                               adv_id="creative_id",
#                                               year_month="2012-02",
#                                               start_day=1,
#                                               end_day=31)
    #print val
#print obj
# StatsModelQueryManager.update_counts(creative_id="creative_id", 
#                                      adgroup_id="adgroup_id", 
#                                      campaign_id="campaign_id",
#                                      adunit_id="adunit_id",
#                                      app_id="app_id",
#                                      fields={'request':1, 'impression':1},
#                                      date_hour = datetime(year=2012,month=10,day=23,hour=11)
#                                      )



#StatsModelQueryManager.get_stats()
#import mongoengine as mdb


# cnt = Cnt()
# Base.objects().update(push__cnts=cnt)

# cnt2 = Cnt2(name="test")
# Base.objects().update(push__cnts__0__cnts2=cnt2)



#stats = StatsModel(dt=date(2011,2,2), pub_id='fake_pub_id', adv_id='adv_id')
# print stats._id
# print stats.dt
# stats.save()
# day_count1 = Counts(day=1)
# day_count2 = Counts(day=2)
# day_count3 = Counts(day=3)
# stats = StatsModel(dt=date(2011,3,3), pub_id='fake_pub_id', adv_id='adv_id', day_counts=[day_count1, day_count2, day_count3])
# stats.save()
# hour_count = HourCounts(hour=15, day=1)
# StatsModel.objects().update(push__hour_counts=hour_count)
# StatsModel.objects().update(push__day_counts=day_count)
#StatsModel.objects().update(push__day_counts__0__hour_counts=hour_count)
#StatsModel.objects().update(set__day_counts__0__day=2)
# # print StatsModel.objects()
# ids = ["2011-03:fake_pub_id:adv_id"]
# x = {'set__day_counts__1__user_count':333444}
# #index = 10000
# #val=333
# stats = StatsModel.objects(_id__in=ids).update(**x)
#print stats
# for stat in stats:
#     break
#


