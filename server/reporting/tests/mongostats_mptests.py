import os
import sys
sys.path.append(os.environ['PWD'])
import common.utils.test.setup

try:
    import json
except ImportError:
    from common.utils import simplejson as json

import datetime
import urlparse
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

from google.appengine.ext import db
from nose.tools import assert_equals

from reporting.models import StatsModel
from reporting.mongostats import _generate_api_url, api_fetch, APIException

def mongostats_api_all_params_mptest():
    # http://mongostats.mopub.com/stats?start_date=111220&end_date=111222&acct=agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww&pub=agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw&adv=agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw
    response = """{"status": 200, "all_stats": {"agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw||agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw||agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww": {"daily_stats": [{"revenue": 2549.2771199999356, "impression_count": 1634152, "conversion_count": 10, "attempt_count": 1283043, "request_count": 0, "click_count": 32907, "unique_users": 1000, "date": "2011-12-20"}, {"revenue": 1342.9150800000045, "impression_count": 860843, "conversion_count": 0, "attempt_count": 736159, "request_count": 0, "click_count": 17645, "unique_users": 2000, "date": "2011-12-21"}, {"revenue": 12.23196000000004, "impression_count": 7841, "conversion_count": 0, "attempt_count": 8220, "request_count": 0, "click_count": 206, "unique_users": 3000, "date": "2011-12-22"}], "sum": {"revenue": 3904.4241599999405, "impression_count": 2502836, "conversion_count": 0, "attempt_count": 2027422, "request_count": 0, "click_count": 50758, "unique_users": 6000}}}}"""

    models = [StatsModel(account = db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                         publisher=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                         advertiser=db.Key('agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw'),
                         revenue= 2549.2771199999356,
                         impression_count= 1634152,
                         conversion_count= 10,
                         request_count= 1283043,
                         click_count= 32907,
                         user_count=1000,
                         date= datetime.datetime(2011,12,20)),
              StatsModel(account = db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                         publisher=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                         advertiser=db.Key('agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw'),
                         revenue= 1342.9150800000045,
                         impression_count= 860843,
                         conversion_count= 0,
                         request_count= 736159,
                         click_count= 17645,
                         user_count=2000,
                         date= datetime.datetime(2011,12,21)),
              StatsModel(account = db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                         publisher=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                         advertiser=db.Key('agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw'),
                         revenue= 12.23196000000004,
                         impression_count= 7841,
                         conversion_count= 0,
                         request_count= 8220,
                         click_count= 206,
                         user_count=3000,
                         date= datetime.datetime(2011,12,22))]

    stats_models = api_fetch(start_date=datetime.date(2011,12,20),
                             end_date=datetime.date(2011,12,22),
                             account_key=db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                             publisher_key=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                             advertiser_key=db.Key('agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw'),
                             response=response)

    assert_equals(models, stats_models)

def mongostats_api_publisher_only_mptest():
    # http://mongostats.mopub.com/stats?start_date=111220&end_date=111222&acct=agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww&pub=agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw&adv=agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw
    response = """{"status": 200, "all_stats": {"agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw||*||agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww": {"daily_stats": [{"revenue": 2549.2771199999356, "impression_count": 1634152, "conversion_count": 10, "attempt_count": 0, "request_count": 1283043, "click_count": 32907, "unique_users": 4000, "date": "2011-12-20"}, {"revenue": 1342.9150800000045, "impression_count": 860843, "conversion_count": 0, "attempt_count": 0, "request_count": 736159, "click_count": 17645, "unique_users": 5000, "date": "2011-12-21"}, {"revenue": 12.23196000000004, "impression_count": 7841, "conversion_count": 0, "attempt_count": 0, "request_count": 8220, "click_count": 206, "unique_users": 6000, "date": "2011-12-22"}], "sum": {"revenue": 3904.4241599999405, "impression_count": 2502836, "conversion_count": 0, "attempt_count": 0, "request_count": 2027422, "click_count": 50758, "unique_users": 15000}}}}"""

    models = [StatsModel(account = db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                         publisher=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                         advertiser=None,
                         revenue= 2549.2771199999356,
                         impression_count= 1634152,
                         conversion_count= 10,
                         request_count= 1283043,
                         click_count= 32907,
                         user_count=4000,
                         date= datetime.datetime(2011,12,20)),
              StatsModel(account = db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                         publisher=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                         advertiser=None,
                         revenue= 1342.9150800000045,
                         impression_count= 860843,
                         conversion_count= 0,
                         request_count= 736159,
                         click_count= 17645,
                         user_count=5000,
                         date= datetime.datetime(2011,12,21)),
              StatsModel(account = db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                         publisher=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                         advertiser=None,
                         revenue= 12.23196000000004,
                         impression_count= 7841,
                         conversion_count= 0,
                         request_count= 8220,
                         click_count= 206,
                         user_count=6000,
                         date= datetime.datetime(2011,12,22))]

    stats_models = api_fetch(start_date=datetime.date(2011,12,20),
                             end_date=datetime.date(2011,12,22),
                             account_key=db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                             publisher_key=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                             advertiser_key=db.Key('agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw'),
                             response=response)

    assert_equals(models, stats_models)


def mongostats_api_account_only_mptest():
    # http://mongostats.mopub.com/stats?start_date=111220&end_date=111222&acct=agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww&pub=agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw&adv=agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw
    response = """{"status": 200, "all_stats": {"*||*||agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww": {"daily_stats": [{"revenue": 2549.2771199999356, "impression_count": 1634152, "conversion_count": 10, "attempt_count": 0, "request_count": 1283043, "click_count": 32907, "unique_users": 11, "date": "2011-12-20"}, {"revenue": 1342.9150800000045, "impression_count": 860843, "conversion_count": 0, "attempt_count": 0, "request_count": 736159, "click_count": 17645, "unique_users": 22, "date": "2011-12-21"}, {"revenue": 12.23196000000004, "impression_count": 7841, "conversion_count": 0, "attempt_count": 0, "request_count": 8220, "click_count": 206, "unique_users": 33, "date": "2011-12-22"}], "sum": {"revenue": 3904.4241599999405, "impression_count": 2502836, "conversion_count": 0, "attempt_count": 0, "request_count": 2027422, "click_count": 50758, "unique_users": 66}}}}"""

    models = [StatsModel(account = db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                         publisher=None,
                         advertiser=None,
                         revenue= 2549.2771199999356,
                         impression_count= 1634152,
                         conversion_count= 10,
                         request_count= 1283043,
                         click_count= 32907,
                         user_count=11,
                         date= datetime.datetime(2011,12,20)),
              StatsModel(account = db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                         publisher=None,
                         advertiser=None,
                         revenue= 1342.9150800000045,
                         impression_count= 860843,
                         conversion_count= 0,
                         request_count= 736159,
                         click_count= 17645,
                         user_count=22,
                         date= datetime.datetime(2011,12,21)),
              StatsModel(account = db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                         publisher=None,
                         advertiser=None,
                         revenue= 12.23196000000004,
                         impression_count= 7841,
                         conversion_count= 0,
                         request_count= 8220,
                         click_count= 206,
                         user_count=33,
                         date= datetime.datetime(2011,12,22))]

    stats_models = api_fetch(start_date=datetime.date(2011,12,20),
                             end_date=datetime.date(2011,12,22),
                             account_key=db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                             publisher_key=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                             advertiser_key=db.Key('agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw'),
                             response=response)

    assert_equals(models, stats_models)


def mongostats_server_error_mptest():
    # http://mongostats.mopub.com/stats?start_date=111220&end_date=111222&acct=agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww&pub=agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw&adv=agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw
    response = "500 response"

    try:
        stats_models = api_fetch(start_date=datetime.date(2011,12,20),
                                 end_date=datetime.date(2011,12,22),
                                 account_key=db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                                 publisher_key=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                                 advertiser_key=db.Key('agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw'),
                                 response=response)
    # idiom to confirm the appropriate exception was raised
    except APIException:
        return
    assert(False, 'APIException not raised')

def api_url_mptest():
    TEST_CASE_URL = "http://mongostats.mopub.com/stats?start_date=111220&end_date=111222&acct=agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww&pub=agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw&adv=agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw&hybrid=True"
    url = _generate_api_url(advertiser_key=db.Key('agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw'),
                            publisher_key=db.Key('agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw'),
                            account_key=db.Key('agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww'),
                            start_date=datetime.date(2011,12,20),
                            end_date=datetime.date(2011,12,22))

    parsed_url = urlparse.urlparse(url)
    parsed_test_case = urlparse.urlparse(TEST_CASE_URL)


    # asserts that the URL is the same (it's OK for the get parameters to be
    # in a different order)

    assert_equals(parsed_url.scheme,
                  parsed_test_case.scheme)

    assert_equals(parsed_url.hostname,
                  parsed_test_case.hostname)

    assert_equals(parsed_url.path,
                  parsed_test_case.path)

    assert_equals(parse_qs(parsed_url.query),
                  parse_qs(parsed_test_case.query))
