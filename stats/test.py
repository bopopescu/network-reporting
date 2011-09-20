from models import StatsModel
from datetime import date, datetime
from utils.mongo_connection import ensure_connection

ensure_connection()
stats = StatsModel(dt=date(2011,2,2), pub_id='fake_pub_id', adv_id='adv_id')
print stats._id
print stats.dt
stats.save()
stats = StatsModel.objects()[0]
print stats.dt
