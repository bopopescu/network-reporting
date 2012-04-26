import os
import sys

sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/django")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/webob")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/yaml/lib")
sys.path.append("/Applications/GoogleAppEngineLauncher.app/Contents/Resources/GoogleAppEngine-default.bundle/Contents/Resources/google_appengine/lib/fancy_urllib")
sys.path.append('/'.join(os.getcwd().split("/")[:-1]))
sys.path.append('.')

import csv
import datetime

from google.appengine.ext.remote_api import remote_api_stub
from google.appengine.ext import db

from reporting.models import StatsModel

TOTAL = 98

def auth_func():
    return "appenginescaletest@gmail.com", "test!@#$"


app_id = 'eventrackerscaletest'
host = '%s.appspot.com' % app_id

remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func, host)

imp_diff = 0
req_diff = 0
clk_diff = 0
conv_diff = 0
stats_dict = {}
for i in range(TOTAL):
  try:
    reader = csv.reader(open('counts_%d.csv'%i, 'rb'), delimiter=' ')
  except:
    reader = []  
  for row in reader:
      req_cnt = int(row[0])
      imp_cnt = int(row[1])
      clk_cnt = int(row[2])
      conv_cnt = int(row[3])
      key_name = row[4]
      # key_parts = key_name.split(':')
      # date_hour = key_parts[1]
      # year = int('20%s'%date_hour[:2])
      # month = int(date_hour[2:4])
      # day = int(date_hour[4:6])
      # hour = int(date_hour[6:8])
      # date_hour = datetime.datetime(year,month,day,hour)
      # date_hour += datetime.timedelta(hours=0)
      # key_parts[1] = date_hour.strftime('%y%m%d%H')
      # key_name = ':'.join(key_parts)
      print '----'
      print key_name
      if not key_name in stats_dict:
        stats_dict[key_name] = {'imp':0,'req':0,'clk':0,'conv':0}
      stats_dict[key_name]['req'] += req_cnt
      stats_dict[key_name]['imp'] += imp_cnt
      stats_dict[key_name]['clk'] += clk_cnt
      stats_dict[key_name]['conv'] += conv_cnt


print stats_dict
for key_name in stats_dict:          
  key = db.Key.from_path('StatsModel','k:ahRldmVudHJhY2tlcnNjYWxldGVzdHIiCxIHQWNjb3VudCIVMTAzNjkzMTc2MzU0MjIwNTAyNDkyDA',
                        'StatsModel',key_name,_app='eventrackerscaletest') 
  stat = StatsModel.get(key)
  print '-'*30
  if stat:
    print key
    print key.name()
    # print client, server
    print stats_dict[key_name]['req'], stat.request_count
    print stats_dict[key_name]['imp'], stat.impression_count
    print stats_dict[key_name]['clk'], stat.click_count
    print stats_dict[key_name]['conv'],stat.conversion_count

    req_diff += stats_dict[key_name]['req'] - stat.request_count
    imp_diff += stats_dict[key_name]['imp'] - stat.impression_count
    clk_diff += stats_dict[key_name]['clk'] - stat.click_count
    conv_diff += stats_dict[key_name]['conv'] - stat.conversion_count 
  else:
      print 'No Stat for key_name %s'%key_name  
print 'request difference: %s'%req_diff                  
print 'impression difference: %s'%imp_diff
