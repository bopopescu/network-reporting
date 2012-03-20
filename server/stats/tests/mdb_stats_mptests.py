import datetime
import logging
import os
import sys
sys.path.append(os.environ['PWD'])
import common.utils.test.setup


from google.appengine.ext import db
from google.appengine.api import users
from nose.tools import assert_equals, assert_not_equals, assert_true, assert_false

from advertiser.models import *
from publisher.models import *
from reporting.models import StatsModel

from common.utils import simplejson
from common.utils.test.test_utils import debug_key_name, debug_helper, add_lists, clear_datastore
from stats.views import _create_mdb_json, _package_mdb_post_data
AdUnit = Site


# start off fresh
clear_datastore()

# create and put model objects
user = users.User(email="test@example.com")
account = Account(key_name="account",user=user).put()

app = App(key_name='app1', name='App',account=account).put()
adunit1 = AdUnit(key_name='adunit1', app_key=app, account=account).put()
adunit2 = AdUnit(key_name='adunit2', app_key=app, account=account).put()

campaign = Campaign(key_name='campaign', name='campaign',account=account, u=user).put()
adgroup = AdGroup(key_name='adgroup', campaign=campaign,account=account).put()
creative1 = Creative(key_name='creative1', ad_group=adgroup,account=account).put()
creative2 = Creative(key_name='creative2', ad_group=adgroup,account=account).put()

# get encoded strings of keys
adunit_id1 = str(adunit1)
adunit_id2 = str(adunit2)
app_id = str(app)
account_id = str(account)
creative_id1 = str(creative1)
creative_id2 = str(creative2)
adgroup_id = str(adgroup)
campaign_id = str(campaign)

# mapping from key to encoded strings; used for debugging messages
id_dict = {adunit_id1: 'adunit_id1',
           adunit_id2: 'adunit_id2',
           app_id: 'app_id',
           creative_id1: 'creative_id1',
           creative_id2: 'creative_id2',
           adgroup_id: 'adgroup_id',
           campaign_id: 'campaign_id',
           '': '',
           'k': 'k'}


# date_hours: first and last hours of a day
hour1 = datetime.datetime(2011, 03, 21, 01)
hour2 = datetime.datetime(2011, 03, 21, 23)

# count lists
# [req, attempt, imp, clk, conv, rev]
# note that xx_c1_xx_xx and xx_c2_xx_xx have the same req count

a1_c1_h1_us = [0, 22, 14, 5, 1, 2.4]
a1_c1_h1_gb = [0, 47, 35, 14, 8, 10.2]
a1_c1_h2_us = [0, 11, 8, 3, 0, 1.8]
a1_c1_h2_gb = [0, 120, 95, 75, 20, 35.6]

a1_c2_h1_us = [0, 15, 9, 0, 0, 0.0]
a1_c2_h1_gb = [0, 18, 11, 2, 1, 17.3]
a1_c2_h2_us = [0, 9, 3, 1, 1, 3.1]
a1_c2_h2_gb = [0, 174, 123, 34, 11, 53.4]

a2_c1_h1_us = [0, 31, 11, 3, 0, 8.4]
a2_c1_h1_gb = [0, 70, 30, 10, 2, 7.2]
a2_c1_h2_us = [0, 91, 53, 23, 10, 11.8]
a2_c1_h2_gb = [0, 150, 105, 55, 2, 25.6]

a2_c2_h1_us = [0, 37, 19, 10, 0, 8.8]
a2_c2_h1_gb = [0, 65, 31, 12, 1, 11.8]
a2_c2_h2_us = [0, 87, 53, 21, 14, 43.5]
a2_c2_h2_gb = [0, 180, 150, 15, 0, 73.2]

a1_xx_h1_us = [10, 0, 0, 0, 0, 0]
a1_xx_h1_gb = [30, 0, 0, 0, 0, 0]
a1_xx_h2_us = [5, 0, 0, 0, 0, 0]
a1_xx_h2_gb = [80, 0, 0, 0, 0, 0]

a2_xx_h1_us = [20, 0, 0, 0, 0, 0]
a2_xx_h1_gb = [45, 0, 0, 0, 0, 0]
a2_xx_h2_us = [50, 0, 0, 0, 0, 0]
a2_xx_h2_gb = [75, 0, 0, 0, 0, 0]


# create base stats models across all dims: adunit X creative X  hour X country
# xx for creative means there's no creative specified, i.e. it's a REQUEST: /m/ad
# note that for request_count, replacing c1 with c2 in count array's name also works

# a1 x h1: REQUESTS
sm_a1_xx_h1_us = StatsModel(publisher=adunit1, date_hour=hour1, country='US', request_count=a1_xx_h1_us[0])
sm_a1_xx_h1_gb = StatsModel(publisher=adunit1, date_hour=hour1, country='GB', request_count=a1_xx_h1_gb[0])

# a1 x h2: REQUESTS
sm_a1_xx_h2_us = StatsModel(publisher=adunit1, date_hour=hour2, country='US', request_count=a1_xx_h2_us[0])
sm_a1_xx_h2_gb = StatsModel(publisher=adunit1, date_hour=hour2, country='GB', request_count=a1_xx_h2_gb[0])

# a2 x h1: REQUESTS
sm_a2_xx_h1_us = StatsModel(publisher=adunit2, date_hour=hour1, country='US', request_count=a2_xx_h1_us[0])
sm_a2_xx_h1_gb = StatsModel(publisher=adunit2, date_hour=hour1, country='GB', request_count=a2_xx_h1_gb[0])

# a2 x h2: REQUESTS
sm_a2_xx_h2_us = StatsModel(publisher=adunit2, date_hour=hour2, country='US', request_count=a2_xx_h2_us[0])
sm_a2_xx_h2_gb = StatsModel(publisher=adunit2, date_hour=hour2, country='GB', request_count=a2_xx_h2_gb[0])

# ADUNIT 1

# a1 x c1 x h1
sm_a1_c1_h1_us = StatsModel(publisher=adunit1, advertiser=creative1, date_hour=hour1, country='US',
                            request_count=a1_c1_h1_us[1],
                            impression_count=a1_c1_h1_us[2],
                            click_count=a1_c1_h1_us[3],
                            conversion_count=a1_c1_h1_us[4],
                            revenue=a1_c1_h1_us[5]
                            )
sm_a1_c1_h1_gb = StatsModel(publisher=adunit1, advertiser=creative1, date_hour=hour1, country='GB',
                            request_count=a1_c1_h1_gb[1],
                            impression_count=a1_c1_h1_gb[2],
                            click_count=a1_c1_h1_gb[3],
                            conversion_count=a1_c1_h1_gb[4],
                            revenue=a1_c1_h1_gb[5]
                            )

# a1 x c1 x h2
sm_a1_c1_h2_us = StatsModel(publisher=adunit1, advertiser=creative1, date_hour=hour2, country='US',
                            request_count=a1_c1_h2_us[1],
                            impression_count=a1_c1_h2_us[2],
                            click_count=a1_c1_h2_us[3],
                            conversion_count=a1_c1_h2_us[4],
                            revenue=a1_c1_h2_us[5])
sm_a1_c1_h2_gb = StatsModel(publisher=adunit1, advertiser=creative1, date_hour=hour2, country='GB',
                            request_count=a1_c1_h2_gb[1],
                            impression_count=a1_c1_h2_gb[2],
                            click_count=a1_c1_h2_gb[3],
                            conversion_count=a1_c1_h2_gb[4],
                            revenue=a1_c1_h2_gb[5])

# a1 x c2 x h1
sm_a1_c2_h1_us = StatsModel(publisher=adunit1, advertiser=creative2, date_hour=hour1, country='US',
                            request_count=a1_c2_h1_us[1],
                            impression_count=a1_c2_h1_us[2],
                            click_count=a1_c2_h1_us[3],
                            conversion_count=a1_c2_h1_us[4],
                            revenue=a1_c2_h1_us[5]
                            )
sm_a1_c2_h1_gb = StatsModel(publisher=adunit1, advertiser=creative2, date_hour=hour1, country='GB',
                            request_count=a1_c2_h1_gb[1],
                            impression_count=a1_c2_h1_gb[2],
                            click_count=a1_c2_h1_gb[3],
                            conversion_count=a1_c2_h1_gb[4],
                            revenue=a1_c2_h1_gb[5])

# a1 x c2 x h2
sm_a1_c2_h2_us = StatsModel(publisher=adunit1, advertiser=creative2, date_hour=hour2, country='US',
                            request_count=a1_c2_h2_us[1],
                            impression_count=a1_c2_h2_us[2],
                            click_count=a1_c2_h2_us[3],
                            conversion_count=a1_c2_h2_us[4],
                            revenue=a1_c2_h2_us[5])
sm_a1_c2_h2_gb = StatsModel(publisher=adunit1, advertiser=creative2, date_hour=hour2, country='GB',
                            request_count=a1_c2_h2_gb[1],
                            impression_count=a1_c2_h2_gb[2],
                            click_count=a1_c2_h2_gb[3],
                            conversion_count=a1_c2_h2_gb[4],
                            revenue=a1_c2_h2_gb[5])

# ADUNIT 2

# a2 x c1 x h1
sm_a2_c1_h1_us = StatsModel(publisher=adunit2, advertiser=creative1, date_hour=hour1, country='US',
                            request_count=a2_c1_h1_us[1],
                            impression_count=a2_c1_h1_us[2],
                            click_count=a2_c1_h1_us[3],
                            conversion_count=a2_c1_h1_us[4],
                            revenue=a2_c1_h1_us[5]
                            )
sm_a2_c1_h1_gb = StatsModel(publisher=adunit2, advertiser=creative1, date_hour=hour1, country='GB',
                            request_count=a2_c1_h1_gb[1],
                            impression_count=a2_c1_h1_gb[2],
                            click_count=a2_c1_h1_gb[3],
                            conversion_count=a2_c1_h1_gb[4],
                            revenue=a2_c1_h1_gb[5]
                            )

# a2 x c1 x h2
sm_a2_c1_h2_us = StatsModel(publisher=adunit2, advertiser=creative1, date_hour=hour2, country='US',
                            request_count=a2_c1_h2_us[1],
                            impression_count=a2_c1_h2_us[2],
                            click_count=a2_c1_h2_us[3],
                            conversion_count=a2_c1_h2_us[4],
                            revenue=a2_c1_h2_us[5]
                            )
sm_a2_c1_h2_gb = StatsModel(publisher=adunit2, advertiser=creative1, date_hour=hour2, country='GB',
                            request_count=a2_c1_h2_gb[1],
                            impression_count=a2_c1_h2_gb[2],
                            click_count=a2_c1_h2_gb[3],
                            conversion_count=a2_c1_h2_gb[4],
                            revenue=a2_c1_h2_gb[5]
                            )

# a2 x c2 x h1
sm_a2_c2_h1_us = StatsModel(publisher=adunit2, advertiser=creative2, date_hour=hour1, country='US',
                            request_count=a2_c2_h1_us[1],
                            impression_count=a2_c2_h1_us[2],
                            click_count=a2_c2_h1_us[3],
                            conversion_count=a2_c2_h1_us[4],
                            revenue=a2_c2_h1_us[5])
sm_a2_c2_h1_gb = StatsModel(publisher=adunit2, advertiser=creative2, date_hour=hour1, country='GB',
                            request_count=a2_c2_h1_gb[1],
                            impression_count=a2_c2_h1_gb[2],
                            click_count=a2_c2_h1_gb[3],
                            conversion_count=a2_c2_h1_gb[4],
                            revenue=a2_c2_h1_gb[5]
                            )

# a2 x c2 x h2
sm_a2_c2_h2_us = StatsModel(publisher=adunit2, advertiser=creative2, date_hour=hour2, country='US',
                            request_count=a2_c2_h2_us[1],
                            impression_count=a2_c2_h2_us[2],
                            click_count=a2_c2_h2_us[3],
                            conversion_count=a2_c2_h2_us[4],
                            revenue=a2_c2_h2_us[5])
sm_a2_c2_h2_gb = StatsModel(publisher=adunit2, advertiser=creative2, date_hour=hour2, country='GB',
                            request_count=a2_c2_h2_gb[1],
                            impression_count=a2_c2_h2_gb[2],
                            click_count=a2_c2_h2_gb[3],
                            conversion_count=a2_c2_h2_gb[4],
                            revenue=a2_c2_h2_gb[5])


def mdb_handler_endpoint_mptest():
    stats_to_put = []
    stats_to_put.extend([sm_a1_xx_h1_us, sm_a1_xx_h1_gb])
    stats_to_put.extend([sm_a1_xx_h2_us, sm_a1_xx_h2_gb])
    stats_to_put.extend([sm_a2_xx_h1_us, sm_a2_xx_h1_gb])
    stats_to_put.extend([sm_a2_xx_h2_us, sm_a2_xx_h2_gb])
    stats_to_put.extend([sm_a1_c1_h1_us, sm_a1_c1_h1_gb])
    stats_to_put.extend([sm_a1_c1_h2_us, sm_a1_c1_h2_gb])
    stats_to_put.extend([sm_a1_c2_h1_us, sm_a1_c2_h1_gb])
    stats_to_put.extend([sm_a1_c2_h2_us, sm_a1_c2_h2_gb])
    stats_to_put.extend([sm_a2_c1_h1_us, sm_a2_c1_h1_gb])
    stats_to_put.extend([sm_a2_c1_h2_us, sm_a2_c1_h2_gb])
    stats_to_put.extend([sm_a2_c2_h1_us, sm_a2_c2_h1_gb])
    stats_to_put.extend([sm_a2_c2_h2_us, sm_a2_c2_h2_gb])


    mdb_json = _create_mdb_json(stats_to_put)
    mdb_dict = simplejson.loads(mdb_json)


    expected_d = {}
    expected_d['%s:%s:%s'%(adunit_id1, creative_id1, hour1.strftime('%y%m%d%H'))] = add_lists([a1_c1_h1_us, a1_c1_h1_gb])
    expected_d['%s:%s:%s'%(adunit_id1, creative_id1, hour2.strftime('%y%m%d%H'))] = add_lists([a1_c1_h2_us, a1_c1_h2_gb])
    expected_d['%s:%s:%s'%(adunit_id1, creative_id2, hour1.strftime('%y%m%d%H'))] = add_lists([a1_c2_h1_us, a1_c2_h1_gb])
    expected_d['%s:%s:%s'%(adunit_id1, creative_id2, hour2.strftime('%y%m%d%H'))] = add_lists([a1_c2_h2_us, a1_c2_h2_gb])

    expected_d['%s:%s:%s'%(adunit_id2, creative_id1, hour1.strftime('%y%m%d%H'))] = add_lists([a2_c1_h1_us, a2_c1_h1_gb])
    expected_d['%s:%s:%s'%(adunit_id2, creative_id1, hour2.strftime('%y%m%d%H'))] = add_lists([a2_c1_h2_us, a2_c1_h2_gb])
    expected_d['%s:%s:%s'%(adunit_id2, creative_id2, hour1.strftime('%y%m%d%H'))] = add_lists([a2_c2_h1_us, a2_c2_h1_gb])
    expected_d['%s:%s:%s'%(adunit_id2, creative_id2, hour2.strftime('%y%m%d%H'))] = add_lists([a2_c2_h2_us, a2_c2_h2_gb])

    expected_d['%s::%s'%(adunit_id1, hour1.strftime('%y%m%d%H'))] = add_lists([a1_xx_h1_us, a1_xx_h1_gb])
    expected_d['%s::%s'%(adunit_id1, hour2.strftime('%y%m%d%H'))] = add_lists([a1_xx_h2_us, a1_xx_h2_gb])

    expected_d['%s::%s'%(adunit_id2, hour1.strftime('%y%m%d%H'))] = add_lists([a2_xx_h1_us, a2_xx_h1_gb])
    expected_d['%s::%s'%(adunit_id2, hour2.strftime('%y%m%d%H'))] = add_lists([a2_xx_h2_us, a2_xx_h2_gb])

    actual_d = {}
    for k, v in mdb_dict.iteritems():
        print debug_key_name(k, id_dict), v
        actual_d[k] = [v['request_count'], v['attempt_count'], v['impression_count'], v['click_count'], v['conversion_count'], v['revenue']]

    # verify length of mdb_dict
    assert_equals(len(actual_d), len(expected_d))

    # verify content of mdb_dict
    for k in actual_d.keys():
        readable_key_name = debug_key_name(k, id_dict)
        debug_helper(readable_key_name, expected_d[k], actual_d[k])
        assert_equals(actual_d[k], expected_d[k])

    # package mdb_dict into derefed post data for mongoDB update stats handler
    has_err, err_msg, post_data = _package_mdb_post_data(mdb_dict)
    assert_false(has_err)
    assert(err_msg is None)
    assert(post_data is not None)

    expected_mdb_post_list = []
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                   'creative': creative_id1,
                                   'date_hour': hour1.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': adgroup_id,
                                   'campaign': campaign_id,
                                   'request_count': add_lists([a1_c1_h1_us, a1_c1_h1_gb])[0],
                                   'attempt_count': add_lists([a1_c1_h1_us, a1_c1_h1_gb])[1],
                                   'impression_count': add_lists([a1_c1_h1_us, a1_c1_h1_gb])[2],
                                   'click_count': add_lists([a1_c1_h1_us, a1_c1_h1_gb])[3],
                                   'conversion_count': add_lists([a1_c1_h1_us, a1_c1_h1_gb])[4],
                                   'revenue': add_lists([a1_c1_h1_us, a1_c1_h1_gb])[5],
                                  })
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                   'creative': creative_id1,
                                   'date_hour': hour2.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': adgroup_id,
                                   'campaign': campaign_id,
                                   'request_count': add_lists([a1_c1_h2_us, a1_c1_h2_gb])[0],
                                   'attempt_count': add_lists([a1_c1_h2_us, a1_c1_h2_gb])[1],
                                   'impression_count': add_lists([a1_c1_h2_us, a1_c1_h2_gb])[2],
                                   'click_count': add_lists([a1_c1_h2_us, a1_c1_h2_gb])[3],
                                   'conversion_count': add_lists([a1_c1_h2_us, a1_c1_h2_gb])[4],
                                   'revenue': add_lists([a1_c1_h2_us, a1_c1_h2_gb])[5],
                                })
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                   'creative': creative_id2,
                                   'date_hour': hour1.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': adgroup_id,
                                   'campaign': campaign_id,
                                   'request_count': add_lists([a1_c2_h1_us, a1_c2_h1_gb])[0],
                                   'attempt_count': add_lists([a1_c2_h1_us, a1_c2_h1_gb])[1],
                                   'impression_count': add_lists([a1_c2_h1_us, a1_c2_h1_gb])[2],
                                   'click_count': add_lists([a1_c2_h1_us, a1_c2_h1_gb])[3],
                                   'conversion_count': add_lists([a1_c2_h1_us, a1_c2_h1_gb])[4],
                                   'revenue': add_lists([a1_c2_h1_us, a1_c2_h1_gb])[5],
                                  })
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                   'creative': creative_id2,
                                   'date_hour': hour2.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': adgroup_id,
                                   'campaign': campaign_id,
                                   'request_count': add_lists([a1_c2_h2_us, a1_c2_h2_gb])[0],
                                   'attempt_count': add_lists([a1_c2_h2_us, a1_c2_h2_gb])[1],
                                   'impression_count': add_lists([a1_c2_h2_us, a1_c2_h2_gb])[2],
                                   'click_count': add_lists([a1_c2_h2_us, a1_c2_h2_gb])[3],
                                   'conversion_count': add_lists([a1_c2_h2_us, a1_c2_h2_gb])[4],
                                   'revenue': add_lists([a1_c2_h2_us, a1_c2_h2_gb])[5],
                                })

    expected_mdb_post_list.append({'adunit': adunit_id2,
                                   'creative': creative_id1,
                                   'date_hour': hour1.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': adgroup_id,
                                   'campaign': campaign_id,
                                   'request_count': add_lists([a2_c1_h1_us, a2_c1_h1_gb])[0],
                                   'attempt_count': add_lists([a2_c1_h1_us, a2_c1_h1_gb])[1],
                                   'impression_count': add_lists([a2_c1_h1_us, a2_c1_h1_gb])[2],
                                   'click_count': add_lists([a2_c1_h1_us, a2_c1_h1_gb])[3],
                                   'conversion_count': add_lists([a2_c1_h1_us, a2_c1_h1_gb])[4],
                                   'revenue': add_lists([a2_c1_h1_us, a2_c1_h1_gb])[5],
                                  })
    expected_mdb_post_list.append({'adunit': adunit_id2,
                                   'creative': creative_id1,
                                   'date_hour': hour2.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': adgroup_id,
                                   'campaign': campaign_id,
                                   'request_count': add_lists([a2_c1_h2_us, a2_c1_h2_gb])[0],
                                   'attempt_count': add_lists([a2_c1_h2_us, a2_c1_h2_gb])[1],
                                   'impression_count': add_lists([a2_c1_h2_us, a2_c1_h2_gb])[2],
                                   'click_count': add_lists([a2_c1_h2_us, a2_c1_h2_gb])[3],
                                   'conversion_count': add_lists([a2_c1_h2_us, a2_c1_h2_gb])[4],
                                   'revenue': add_lists([a2_c1_h2_us, a2_c1_h2_gb])[5],
                                })
    expected_mdb_post_list.append({'adunit': adunit_id2,
                                   'creative': creative_id2,
                                   'date_hour': hour1.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': adgroup_id,
                                   'campaign': campaign_id,
                                   'request_count': add_lists([a2_c2_h1_us, a2_c2_h1_gb])[0],
                                   'attempt_count': add_lists([a2_c2_h1_us, a2_c2_h1_gb])[1],
                                   'impression_count': add_lists([a2_c2_h1_us, a2_c2_h1_gb])[2],
                                   'click_count': add_lists([a2_c2_h1_us, a2_c2_h1_gb])[3],
                                   'conversion_count': add_lists([a2_c2_h1_us, a2_c2_h1_gb])[4],
                                   'revenue': add_lists([a2_c2_h1_us, a2_c2_h1_gb])[5],
                                  })
    expected_mdb_post_list.append({'adunit': adunit_id2,
                                   'creative': creative_id2,
                                   'date_hour': hour2.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': adgroup_id,
                                   'campaign': campaign_id,
                                   'request_count': add_lists([a2_c2_h2_us, a2_c2_h2_gb])[0],
                                   'attempt_count': add_lists([a2_c2_h2_us, a2_c2_h2_gb])[1],
                                   'impression_count': add_lists([a2_c2_h2_us, a2_c2_h2_gb])[2],
                                   'click_count': add_lists([a2_c2_h2_us, a2_c2_h2_gb])[3],
                                   'conversion_count': add_lists([a2_c2_h2_us, a2_c2_h2_gb])[4],
                                   'revenue': add_lists([a2_c2_h2_us, a2_c2_h2_gb])[5],
                                })

    expected_mdb_post_list.append({'adunit': adunit_id1,
                                   'creative': '',
                                   'date_hour': hour1.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': None,
                                   'campaign': None,
                                   'request_count': add_lists([a1_xx_h1_us, a1_xx_h1_gb])[0],
                                   'attempt_count': 0,
                                   'impression_count': 0,
                                   'click_count': 0,
                                   'conversion_count': 0,
                                   'revenue': 0,
                                  })
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                   'creative': '',
                                   'date_hour': hour2.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': None,
                                   'campaign': None,
                                   'request_count': add_lists([a1_xx_h2_us, a1_xx_h2_gb])[0],
                                   'attempt_count': 0,
                                   'impression_count': 0,
                                   'click_count': 0,
                                   'conversion_count': 0,
                                   'revenue': 0,
                                })
    expected_mdb_post_list.append({'adunit': adunit_id2,
                                   'creative': '',
                                   'date_hour': hour1.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': None,
                                   'campaign': None,
                                   'request_count': add_lists([a2_xx_h1_us, a2_xx_h1_gb])[0],
                                   'attempt_count': 0,
                                   'impression_count': 0,
                                   'click_count': 0,
                                   'conversion_count': 0,
                                   'revenue': 0,
                                  })
    expected_mdb_post_list.append({'adunit': adunit_id2,
                                   'creative': '',
                                   'date_hour': hour2.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': None,
                                   'campaign': None,
                                   'request_count': add_lists([a2_xx_h2_us, a2_xx_h2_gb])[0],
                                   'attempt_count': 0,
                                   'impression_count': 0,
                                   'click_count': 0,
                                   'conversion_count': 0,
                                   'revenue': 0,
                                })

    mdb_post_list = simplejson.loads(post_data)
    assert_equals(len(mdb_post_list), len(expected_mdb_post_list))

    for post_dict in mdb_post_list:
        assert(post_dict in expected_mdb_post_list) # assert dict exists in expected list
        expected_mdb_post_list.remove(post_dict)    # remove found dict in expected list to avoid dups

    assert_equals(len(expected_mdb_post_list), 0)   # assert all dicts were found



def mdb_handler_endpoint_mptest_req_only():
    # requests only
    mdb_json = _create_mdb_json([sm_a1_xx_h1_us, sm_a1_xx_h1_gb, sm_a1_xx_h2_us, sm_a1_xx_h2_gb])
    mdb_dict = simplejson.loads(mdb_json)

    expected_d = {}
    expected_d['%s::%s'%(adunit_id1, hour1.strftime('%y%m%d%H'))] = add_lists([a1_xx_h1_us, a1_xx_h1_gb])
    expected_d['%s::%s'%(adunit_id1, hour2.strftime('%y%m%d%H'))] = add_lists([a1_xx_h2_us, a1_xx_h2_gb])

    actual_d = {}
    for k, v in mdb_dict.iteritems():
        print debug_key_name(k, id_dict), v
        actual_d[k] = [v['request_count'], v['attempt_count'], v['impression_count'], v['click_count'], v['conversion_count'], v['revenue']]

    # verify length of mdb_dict
    assert_equals(len(actual_d), len(expected_d))

    # verify content of mdb_dict
    for k in actual_d.keys():
        readable_key_name = debug_key_name(k, id_dict)
        debug_helper(readable_key_name, expected_d[k], actual_d[k])
        assert_equals(actual_d[k], expected_d[k])

    # package mdb_dict into derefed post data for mongoDB update stats handler
    has_err, err_msg, post_data = _package_mdb_post_data(mdb_dict)
    assert_false(has_err)
    assert(err_msg is None)
    assert(post_data is not None)

    expected_mdb_post_list = []
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                   'creative': '',
                                   'date_hour': hour1.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': None,
                                   'campaign': None,
                                   'request_count': add_lists([a1_xx_h1_us, a1_xx_h1_gb])[0],
                                   'attempt_count': 0,
                                   'impression_count': 0,
                                   'click_count': 0,
                                   'conversion_count': 0,
                                   'revenue': 0,
                                  })
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                 'creative': '',
                                 'date_hour': hour2.strftime('%y%m%d%H'),
                                 'app': app_id,
                                 'account': account_id,
                                 'adgroup': None,
                                 'campaign': None,
                                 'request_count': add_lists([a1_xx_h2_us, a1_xx_h2_gb])[0],
                                 'attempt_count': 0,
                                 'impression_count': 0,
                                 'click_count': 0,
                                 'conversion_count': 0,
                                 'revenue': 0,
                                })

    mdb_post_list = simplejson.loads(post_data)
    assert_equals(len(mdb_post_list), len(expected_mdb_post_list))

    for post_dict in mdb_post_list:
        assert(post_dict in expected_mdb_post_list) # assert dict exists in expected list
        expected_mdb_post_list.remove(post_dict)    # remove found dict in expected list to avoid dups

    assert_equals(len(expected_mdb_post_list), 0)   # assert all dicts were found



def mdb_handler_endpoint_mptest_mixed():
    stats_to_put = []
    stats_to_put.extend([sm_a1_xx_h1_us, sm_a1_xx_h1_gb, sm_a1_xx_h2_us, sm_a1_xx_h2_gb])   # req only
    stats_to_put.extend([sm_a1_c1_h1_us, sm_a1_c2_h2_gb])

    mdb_json = _create_mdb_json(stats_to_put)
    mdb_dict = simplejson.loads(mdb_json)

    expected_d = {}
    expected_d['%s::%s'%(adunit_id1, hour1.strftime('%y%m%d%H'))] = add_lists([a1_xx_h1_us, a1_xx_h1_gb])
    expected_d['%s::%s'%(adunit_id1, hour2.strftime('%y%m%d%H'))] = add_lists([a1_xx_h2_us, a1_xx_h2_gb])
    expected_d['%s:%s:%s'%(adunit_id1, creative_id1, hour1.strftime('%y%m%d%H'))] = a1_c1_h1_us
    expected_d['%s:%s:%s'%(adunit_id1, creative_id2, hour2.strftime('%y%m%d%H'))] = a1_c2_h2_gb


    actual_d = {}
    for k, v in mdb_dict.iteritems():
        print debug_key_name(k, id_dict), v
        actual_d[k] = [v['request_count'], v['attempt_count'], v['impression_count'], v['click_count'], v['conversion_count'], v['revenue']]

    # verify length of mdb_dict
    assert_equals(len(actual_d), len(expected_d))

    # verify content of mdb_dict
    for k in actual_d.keys():
        readable_key_name = debug_key_name(k, id_dict)
        debug_helper(readable_key_name, expected_d[k], actual_d[k])
        assert_equals(actual_d[k], expected_d[k])

    # package mdb_dict into derefed post data for mongoDB update stats handler
    has_err, err_msg, post_data = _package_mdb_post_data(mdb_dict)
    assert_false(has_err)
    assert(err_msg is None)
    assert(post_data is not None)

    expected_mdb_post_list = []
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                   'creative': creative_id1,
                                   'date_hour': hour1.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': adgroup_id,
                                   'campaign': campaign_id,
                                   'request_count': a1_c1_h1_us[0],
                                   'attempt_count': a1_c1_h1_us[1],
                                   'impression_count': a1_c1_h1_us[2],
                                   'click_count': a1_c1_h1_us[3],
                                   'conversion_count': a1_c1_h1_us[4],
                                   'revenue': a1_c1_h1_us[5],
                                  })
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                 'creative': creative_id2,
                                 'date_hour': hour2.strftime('%y%m%d%H'),
                                 'app': app_id,
                                 'account': account_id,
                                 'adgroup': adgroup_id,
                                 'campaign': campaign_id,
                                 'request_count': a1_c2_h2_gb[0],
                                 'attempt_count': a1_c2_h2_gb[1],
                                 'impression_count': a1_c2_h2_gb[2],
                                 'click_count': a1_c2_h2_gb[3],
                                 'conversion_count': a1_c2_h2_gb[4],
                                 'revenue': a1_c2_h2_gb[5],
                                })
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                   'creative': '',
                                   'date_hour': hour1.strftime('%y%m%d%H'),
                                   'app': app_id,
                                   'account': account_id,
                                   'adgroup': None,
                                   'campaign': None,
                                   'request_count': add_lists([a1_xx_h1_us, a1_xx_h1_gb])[0],
                                   'attempt_count': 0,
                                   'impression_count': 0,
                                   'click_count': 0,
                                   'conversion_count': 0,
                                   'revenue': 0,
                                  })
    expected_mdb_post_list.append({'adunit': adunit_id1,
                                 'creative': '',
                                 'date_hour': hour2.strftime('%y%m%d%H'),
                                 'app': app_id,
                                 'account': account_id,
                                 'adgroup': None,
                                 'campaign': None,
                                 'request_count': add_lists([a1_xx_h2_gb, a1_xx_h2_us])[0],
                                 'attempt_count': 0,
                                 'impression_count': 0,
                                 'click_count': 0,
                                 'conversion_count': 0,
                                 'revenue': 0,
                                })

    mdb_post_list = simplejson.loads(post_data)
    assert_equals(len(mdb_post_list), len(expected_mdb_post_list))

    for post_dict in mdb_post_list:
        assert(post_dict in expected_mdb_post_list) # assert dict exists in expected list
        expected_mdb_post_list.remove(post_dict)    # remove found dict in expected list to avoid dups

    assert_equals(len(expected_mdb_post_list), 0)   # assert all dicts were found



def package_mdb_post_data_bad_key_mptest():
    mdb_dict_with_bad_key = {'adunit:creative:date_hour:crap': {}}  # has extra part
    has_err, err_msg, post_data = _package_mdb_post_data(mdb_dict_with_bad_key)
    assert_true(has_err)
    assert('Error parsing' in err_msg)
    assert(post_data is None)

    mdb_dict_with_bad_key = {'adunit:date_hour': {}}    # missing creative part
    has_err, err_msg, post_data = _package_mdb_post_data(mdb_dict_with_bad_key)
    assert_true(has_err)
    assert('Error parsing' in err_msg)
    assert(post_data is None)


def package_mdb_post_data_none_deref_mptest():
    mdb_dict_with_invalid_ids = {'adunit:creative:date_hour': {}}  # fake id's, cannot be derefed
    has_err, err_msg, post_data = _package_mdb_post_data(mdb_dict_with_invalid_ids)
    assert_true(has_err)
    assert('None derefed' in err_msg)
    assert(post_data is None)
