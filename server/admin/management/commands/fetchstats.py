import sys
import datetime

from django.core.management.base import BaseCommand

from account.query_managers import AccountQueryManager
from reporting.query_managers import StatsModelQueryManager
from common.utils.timezones import Pacific_tzinfo
from common.utils import date_magic

try:
    from clint.textui import puts, indent, colored
except ImportError:
    print 'please install clint (pip install clint)'


USAGE="""
fetchstats - fetches stats from mongo and prints them out.
usage: ./manage.py fetchstats --account=<email> [--publisher=<key>] [--advertiser=<key>]
one of (account, publisher, advertiser) needs to be set.

you can also supply:
- start_date
- end_date
- date_range

if none are supplied, end_date defaults to today, date_range defaults
to 14, and start_date defaults to 14 days ago (works just like the
date buttons in the website).
"""

class Command(BaseCommand):
    """
    Fetches stats from mongo and prints them beautifully on the command
    line
    """
    def run_from_argv(self, argv):
        try:
            arguments = argv[2:]
        except IndexError:
            print 'you screwed it up fool.'
            print USAGE
            sys.exit(1)

        # stuff we need to fetch stats
        account, publisher, advertiser = None, None, None
        date_range, start_date, end_date = None, None, None

        # parse args
        for argument in arguments:
            if argument.find('--account=') == 0:
                print 'fuck to you'
                account = argument[10:]
            elif argument.find('--publisher=') == 0:
                publisher = argument[12:]
            elif argument.find('--advertiser=') == 0:
                advertiser = argument[13:]
            elif argument.find('--date_range=') == 0:
                date_range = argument[13:]

        # set defaults for the date range
        date_range = date_range or 14
        end_date = end_date or \
                   datetime.datetime.now(Pacific_tzinfo()).date()
        start_date = start_date or end_date -  \
                     datetime.timedelta(date_range - date_range)

        days = date_magic.gen_days(start_date, end_date)

        account_obj = AccountQueryManager.get_account_for_email(account)

        print account, publisher, advertiser
        # fetch stats
        if account and (publisher or advertiser):
            qm = StatsModelQueryManager(account_obj)
            stats = qm.get_stats_for_days(publisher=publisher,
                                          advertiser=advertiser,
                                          use_mongo=True)
        else:
            print 'you screwed it up fool.'
            print USAGE
            sys.exit(1)

        # display that shit
        print stats


