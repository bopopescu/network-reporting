import datetime
try:
    import json
except ImportError:
    from common.utils import simplejson as json
import urllib
import urllib2

from google.appengine.ext import db

from reporting.models import StatsModel

BASE_URL = 'http://mongostats.mopub.com/stats'
DELIM = '||'

def api_fetch(start_date, end_date,
              account_key=None, publisher_key=None,
              advertiser_key=None, response=None):
    """
    Hits the mongostats API and converts the response into StatsModels

    Return: a list of StatsModel(s)
    """
    if not response: # used for testing only
        url = _generate_api_url(start_date, end_date,
                                account_key, publisher_key,
                                advertiser_key)
        response = urllib2.urlopen(url).read()

    try:
        response_dict = json.loads(response)
    except ValueError: #invalid JSON
        raise(APIException('invalid JSON returned from server'))

    status = response_dict['status']
    if status != 200:
        raise(APIException('status = %s' % status))

    stats_models = [] # list of 'StatsModel's to be returned

    all_stats = response_dict['all_stats'] # dictionary

    for key in all_stats:
        #
        # key e.g. agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw||agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw||agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww pylint: disable=C0301
        pub_str, adv_str, acct_str = key.split(DELIM)
        daily_stats = all_stats[key]['daily_stats'] # list of dictionaries

        for stats_dict in daily_stats:
            # stats_dict - e.g.
            # {'attempt_count': 1283043,
            # 'click_count': 32907,
            # 'conversion_count': 0,
            # 'date': '2011-12-20',
            # 'impression_count': 1634152,
            # 'request_count': 0,
            # 'revenue': 2549.2771199999356,
            # 'unique_users': 318572}

            advertiser = _key_or_none(adv_str)
            # Since request_count is overloaded we must
            # use attempt_count (from) as request_count if
            # the advertiser field is present else we just
            # use request_count
            if advertiser:
                request_count = stats_dict['attempt_count']
            else:
                request_count = stats_dict['request_count']

            stats_model = StatsModel(account=_key_or_none(acct_str),
                             publisher=_key_or_none(pub_str),
                             advertiser=advertiser,
                             date=_datetime_from_str(stats_dict['date']),
                             request_count=int(request_count),
                             impression_count=int(stats_dict['impression_count']),
                             click_count=int(stats_dict['click_count']),
                             conversion_count=int(stats_dict['conversion_count']),
                             user_count=int(stats_dict['unique_users']),
                             revenue=float(stats_dict['revenue']))
            stats_models.append(stats_model)
    return stats_models

def _generate_api_url(start_date, end_date,
                      account_key=None, publisher_key=None,
                      advertiser_key=None):
    """
    generates a url of the form:
    http://mongostats.mopub.com/stats?start_date=111220&end_date=111222&acct=agltb3B1Yi1pbmNyEAsSB0FjY291bnQY8d77Aww&pub=agltb3B1Yi1pbmNyDQsSBFNpdGUY9IiEBAw&adv=agltb3B1Yi1pbmNyEAsSB0FkR3JvdXAYw5TmBAw
    """
    params = {
        "start_date": _format_date(start_date),
        "end_date": _format_date(end_date),
        "acct": _str_or_empty(account_key),
        "pub": _str_or_empty(publisher_key),
        "adv": _str_or_empty(advertiser_key),
    }

    query_string = urllib.urlencode(params)

    return BASE_URL + '?' + query_string

class APIException(Exception):
    pass

def _format_date(date_):
    """
    Formats the date like YYMMDD
    """
    return date_.strftime("%y%m%d")

def _datetime_from_str(date_string):
    """
    date_string e.g. YYYY-MM-DD
    """
    return datetime.datetime.strptime(date_string, '%Y-%m-%d')

def _str_or_empty(key):
    """
    Stringifies the key or return the empty string
    """
    return str(key) if key else ''

def _key_or_none(key_string):
    """
    Returns a db.Key object of the string representation of the string
    NOTE: the api returns '*' (i.e. wildcard) when the key should be None
    """
    return db.Key(key_string) if key_string and key_string != '*' else None
