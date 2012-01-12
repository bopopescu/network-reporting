#!/usr/bin/python

import logging
import os
import sys
import traceback

# Are we on EC2 (Note can't use django.settings_module since it's not defined)
if os.path.exists('/home/ubuntu/'):
    sys.path.append('/home/ubuntu/mopub/server')
    sys.path.append('/home/ubuntu/google_appengine')
    sys.path.append('/home/ubuntu/google_appengine/lib/antlr3')
    sys.path.append('/home/ubuntu/google_appengine/lib/django_1_2')
    sys.path.append('/home/ubuntu/google_appengine/lib/fancy_urllib')
    sys.path.append('/home/ubuntu/google_appengine/lib/ipaddr')
    sys.path.append('/home/ubuntu/google_appengine/lib/webob')
    sys.path.append('/home/ubuntu/google_appengine/lib/yaml/lib')
else:
    # Assumes it is being called from ./run_tests.sh from server dir
    sys.path.append('/Users/tiagobandeira/Documents/mopub/server')
    #sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from multiprocessing import Process, Queue
import unicodedata, re

from google.appengine.api import mail

from datetime import date, datetime, timedelta

from ad_network_reports.ad_networks import AdNetwork
from ad_network_reports.models import AdNetworkAppMapper, \
        AdNetworkScrapeStats, \
        AdNetworkManagementStats
from ad_network_reports.query_managers import \
        AD_NETWORK_NAMES, \
        IAD, \
        MOBFOX, \
        AdNetworkLoginCredentialsManager, \
        AdNetworkMapperManager, \
        AdNetworkStatsManager, \
        AdNetworkManagementStatsManager
from ad_network_reports.scrapers.unauthorized_login_exception import \
        UnauthorizedLogin
from common.utils import date_magic
from common.utils.connect_to_appengine import setup_remote_api
from publisher.query_managers import AppQueryManager
from pytz import timezone

from google.appengine.ext import db

TESTING = True

MAX = 1000
BUFFER = 200


def multiprocess_update_all(start_day=None, end_day=None, email=True,
        processes=1):
    """
    Break up update script into multiple processes.
    """
    # Standardize the date
    pacific = timezone('US/Pacific')
    yesterday = (datetime.now(pacific) - timedelta(days=1)).date()

    # Set start and end dates
    start_day = start_day or yesterday
    end_day = end_day or yesterday

    login_count = AdNetworkLoginCredentialsManager.get_all_logins().count()

    # Calculate the range (# of logins each process must handle) and the
    # remainder (# of additional logins the last process must handle)
    if processes > login_count:
        processes = login_count
    range_ = int(login_count / processes)
    remainder = login_count % processes

    # create multiprocess queue to store management stats
    queue = Queue()

    children = []
    for num in range(processes):
        # Create a log file
        info = (num,
                start_day.strftime('%Y_%m_%d'),
                end_day.strftime('%Y_%m_%d'),)
        logger = create_logger('update_p%d_%s_to_%s_log' % info, '/var/tmp/update_p%d_%s_to_%s.log'
                % info)

        # Calculate offset
        offset = range_ * num

        # If we are creating the last process include the remainder
        if num == processes - 1:
            range_ += remainder

        logger.info("Starting process %d with offset %d and range %d" % (num,
            offset, range_))

        # Spawn off new process calling update_all and giving it it's
        # appropriate offset (start point) and range
        process = Process(target=update_all,
                kwargs={'start_day': start_day,
                        'end_day': end_day,
                        'logger': logger,
                        'offset': offset,
                        'range_': range_,
                        'queue': queue})
        process.start()
        children.append(process)

    # Wait for all processes to complete
    for process in children:
        process.join()

    # Save management stats
    stats_dict = {}
    while queue.full():
        stats = queue.get()
        if stats.day in stats_dict:
            stats_dict[stats.day].combined(stats)
        else:
            stats_dict[stats.day] = stats

    for stats in stats_dict.itervalues():
        stats.put_stats()

    # Email accounts
    if email:
        for day in date_magic.gen_days(start_day, end_day):
            send_emails(day)


def update_all(start_day=None, end_day=None, logger=None, offset=0, range_=-1, queue=None):
    """Update all ad network stats.

    Iterate through all AdNetworkLoginCredentials. Login to the ad networks
    saving the data for the date range in the db.

    Run daily as a cron job in EC2. Email Tiago if errors occur.
    """
    if range_ == -1:
        range_ = AdNetworkLoginCredentialsManager.get_all_logins().count()

    # Standardize the date
    pacific = timezone('US/Pacific')
    yesterday = (datetime.now(pacific) - timedelta(days=1)).date()

    logins_query = AdNetworkLoginCredentialsManager.get_all_logins()
    limit = min(range_, MAX)
    count = limit
    logins = logins_query.fetch(limit, offset=offset)

    # Set start and end dates
    start_day = start_day or yesterday
    end_day = end_day or yesterday

    stats_list = []
    # Iterate through date range
    for day in date_magic.gen_days(start_day, end_day):
        if logger:
            logger.info("TEST DATE: %s" % day.strftime("%Y %m %d"))
        # Create Management Stats
        management_stats = AdNetworkManagementStatsManager(day=day)

        while logins:
            # Iterate through logins
            for login in logins:
                stats_list += update_login_stats(login, day, management_stats, logger, queue)

                # Flush stats_list to the database
                if len(stats_list) > MAX - BUFFER:
                    db.put(stats_list)
                    stats_list = []

            # Update logins
            db.put(logins)

            # Get the next set of logins
            if range_ > count:
                limit = min(range_ - count, MAX)
                count += limit
                logins = bulk_get(logins_query, login, limit=limit)
            else:
                logins = []


        queue.put(management_stats)
    # Flush the remaining stats to the db
    db.put([stats for mapper, stats in stats_list])


def update_login_stats_for_check(login, start_day=None, end_day=None):
    """
    Collect data for a given login from the start date to yesterday.

    Send email to account when complete if stats have been collected.
    """
    # Standardize the date
    pacific = timezone('US/Pacific')
    yesterday = (datetime.now(pacific) - timedelta(days=1)).date()

    # Set start and end dates
    start_day = start_day or yesterday
    end_day = end_day or yesterday

    stats_list = []
    for day in date_magic.gen_days(start_day, yesterday):
        stats_list += update_login_stats(login, day)
    login.put()

    if stats_list:
        # Flush stats to db
        db.put([stats for mapper, stats in stats_list])

        # Send email informing user that they can now see statistics for the ad
        # network they just signed up for on the ad network index page.
        emails = ', '.join(getattr(login.account, 'ad_network_emails', []))
        if not emails:
            emails = ', '.join(login.account.emails)

        mail.send_mail(sender='olp@mopub.com',
                       reply_to='support@mopub.com',
                       to='tiago@mopub.com' if TESTING else emails,
                       bcc='tiago@mopub.com',
                       subject="Finished Collecting Stats",
                       body="Your ad network revenue report for %s is now ready. " \
                               "Access it here: https://app.mopub.com/ad_network_reports.\n\n" \
                               "If you have any questions, please reach out to us at support@mopub.com" \
                               % AD_NETWORK_NAMES[login.ad_network_name])


def update_login_stats(login, day, management_stats=None, logger=None, queue=None):
    """
    Update or create stats for the given login and day.

    Login to the network pull stats from api or page

    Return list of mapper and scrape stats objects.
    """
    # Clear app pub ids from login
    login.app_pub_ids = []

    # Initialize return value
    valid_stats_list = []

    network_name = login.ad_network_name
    try:
        if logger:
            logger.info("Creating network")
        # AdNetwork is a factory class that returns the appropriate
        # subclass of itself when created.
        network = AdNetwork(login)

        network.append_extra_info()
        scraper = network.create_scraper()

        # Return a list of NetworkScrapeRecord objects of stats for
        # each app for the day
        stats_list = scraper.get_site_stats(day)
        if logger:
            logger.info("Received stats list")
    except UnauthorizedLogin:
        # Users email changed since we last verified
        if logger:
            logger.info("Unauthorized login attempted by account:%s on %s."
                    % (login.account,
                        login.ad_network_name))
        return []
    except Exception as e:
        # This should catch ANY exception because we don't want to stop
        # updating stats if something minor breaks somewhere.
        if management_stats:
            management_stats.append_failed_login(login)
        # Log the error
        if logger:
            logger.error(("Couldn't get get stats for %s network for "
                    "\"%s\" account.  Can try again later or perhaps %s "
                    "changed it's API or site.") %
                    (login.ad_network_name,
                        login.account.key(),
                        login.ad_network_name))
        exc_traceback = sys.exc_info()[2]
        # Email tiago the traceback
        mail.send_mail(sender='olp@mopub.com',
                       to='tiago@mopub.com',
                       subject=("Ad Network Scrape Error on %s" %
                           day.strftime("%m/%d/%y")),
                       body=("Couldn't get get stats for %s network "
                           "for \"%s\" account. Error:\n %s\n\n"
                           "Traceback:\n%s" % (login.
                               ad_network_name, login.
                               account.key(), e, repr(traceback.
                                   extract_tb(exc_traceback)))))
        return []

    # Iterate through the NSR objects returned by the scraper
    for stats in stats_list:
        if management_stats:
            management_stats.increment(login.ad_network_name,
                    'found')

        if login.ad_network_name == IAD:
            publisher_id = AppQueryManager.get_iad_pub_id(
                    login.account, stats.app_tag)
        else:
            publisher_id = stats.app_tag

        if not publisher_id:
            if stats.app_tag:
                login.app_pub_ids.append(remove_control_chars(stats.app_tag))
            continue

        # Get the mapper object that corresponds to the
        # login and stats.
        mapper = AdNetworkMapperManager. \
                get_ad_network_mapper(publisher_id=publisher_id,
                                      ad_network_name=login.ad_network_name)

        if not mapper:
            # Check if the app has been added to MoPub prior to last
            # update.
            mapper = AdNetworkMapperManager. \
                    find_app_for_stats(publisher_id, login)
            if not mapper:
                # App is not registered in MoPub but is still in the ad
                # network.
                if logger:
                    logger.info("%(account)s has pub id %(pub_id)s on "
                            "%(network)s that\'s NOT in MoPub" %
                                 dict(account=login.account.key(),
                                      pub_id=publisher_id,
                                      network=login.ad_network_name))
                login.app_pub_ids.append(publisher_id)
                continue
            else:
                if management_stats:
                    management_stats.increment(login.ad_network_name, 'mapped')
                if logger:
                    logger.info("%(account)s has pub id %(pub_id)s on "
                            "%(network)s that was FOUND in MoPub and "
                            "mapped" %
                                 dict(account=login.account.
                                     key(),
                                      pub_id=publisher_id,
                                      network=login.ad_network_name))
        elif logger:
            logger.info("%(account)s has pub id %(pub_id)s on "
                    "%(network)s that\'s in MoPub" %
                    dict(account=login.account.key(),
                        pub_id=publisher_id,
                        network=login.ad_network_name))

        if management_stats:
            management_stats.increment(login.ad_network_name, 'updated')

        scrape_stats = AdNetworkScrapeStats(ad_network_app_mapper=mapper,
                                            date=day,
                                            revenue=float(stats.revenue),
                                            attempts=stats.attempts,
                                            impressions=stats.impressions,
                                            clicks=stats.clicks)
        valid_stats_list.append((mapper, scrape_stats))

    return valid_stats_list


## Helpers
#
def bulk_get(query, last_object, limit):
    return query.filter('__key__ >', last_object).fetch(limit)


def send_emails(day):
    logins_query = AdNetworkLoginCredentialsManager.get_all_logins(order_by_account=
            True)

    last_account = None
    for login in logins_query:
        if login.account != last_account:
            last_account = login.account
            if login.email or getattr(login.account,
                    'receive_ad_network_emails', False):
                mappers = AdNetworkMapperManager.get_mappers(login.account)
                stats_list = [AdNetworkStatsManager.get_stats_for_mapper_and_days(mapper,
                    (day,)) for mapper in mappers]
                send_stats_mail(login.account, day, stats_list)


CONTROL_CHARS = ''.join(map(unichr, range(0,32) + range(127,160)))
CONTROL_CHAR_RE = re.compile('[%s]' % re.escape(CONTROL_CHARS))

def remove_control_chars(str_):
    """
    Strip unicode pictures
    """
    return CONTROL_CHAR_RE.sub('', str_)


def send_stats_mail(account, day, stats_list):
    """
    Send email with scrape stats data for the test date organized in a
    table.
    """
    emails = ', '.join(getattr(account, 'ad_network_emails', []))
    if not emails:
        emails = ', '.join(account.emails)

    if emails and stats_list:
        aggregate_stats = AdNetworkStatsManager.roll_up_stats([stats for
            mapper, stats in stats_list])
        stats_list = sorted(stats_list, key = lambda stats:
                '%s-%s-%s' % (stats[0].application.name.lower(),
                stats[0].application.app_type_text().lower(),
                stats[0].ad_network_name))
        email_body = ""
        for mapper, stats in stats_list:
            app_name = '%s (%s)' % (mapper.application.name,
                    mapper.application.app_type_text())

            stats_dict = {'app': app_name,
                   'network_name': AD_NETWORK_NAMES[mapper.ad_network_name],
                   'revenue': stats.revenue,
                   'attempts': stats.attempts,
                   'impressions': stats.impressions,
                   'fill_rate': stats.fill_rate,
                   'clicks': stats.clicks,
                   'ctr': stats.ctr * 100,
                   'cpm': stats.cpm}
            email_body += (("""
            <tr>
                <td>%(app)s</td>
                <td>%(network_name)s</td>
                <td>$%(revenue).2f</td>
                """ +
                ("<td>%(attempts)d</td>" if mapper.ad_network_name != MOBFOX \
                        else "<td></td>") +
                "<td>%(impressions)d</td>" +
                ("<td>%(fill_rate).2f%%</td>" if mapper.ad_network_name != \
                        MOBFOX else "<td></td>") +
                """
                <td>%(clicks)d</td>
                <td>%(ctr).2f%%</td>
                <td>%(cpm).2f</td>
            </tr>
            """) % stats_dict)

        # CSS doesn't work with Gmail so use horrible html style tags ex. <b>
        mail.send_mail(sender='olp@mopub.com',
                reply_to='support@mopub.com',
                to='tiago@mopub.com' if TESTING else emails,
                bcc='tiago@mopub.com' if TESTING else
                    'tiago@mopub.com, report-monitoring@mopub.com',
                subject=("Ad Network Revenue Reporting for %s" %
                                day.strftime("%m/%d/%y")),
                body=("Learn more at https://app.mopub.com/"
                    "ad_network_reports/"),
                html=(
                """
<table width=100%%>
    <thead>
        <th>APP NAME</th>
        <th>AD NETWORK</th>
        <th>REVENUE</th>
        <th>ATTEMPTS</th>
        <th>IMPRESSIONS</th>
        <th>FILLRATE</th>
        <th>CLICKS</th>
        <th>CTR</th>
        <th>CPM</th>
    </thead>
    <tbody>
        <tr>
            <td><b>TOTAL</b></td>
            <td></td>
            <td><b>$%(revenue).2f</b></td>
            <td><b>%(attempts)d</b></td>
            <td><b>%(impressions)d</b></td>
            <td><b>%(fill_rate).2f%%</b></td>
            <td><b>%(clicks)d</b></td>
            <td><b>%(ctr).2f%%</b></td>
            <td><b>%(cpm).2f</b></td>
        </tr>
                    """ % {'revenue': aggregate_stats.revenue,
                           'attempts': aggregate_stats.attempts,
                           'impressions': aggregate_stats.impressions,
                           'fill_rate': aggregate_stats.fill_rate,
                           'clicks': aggregate_stats.clicks,
                           'ctr': aggregate_stats.ctr * 100,
                           'cpm': aggregate_stats.cpm} +
                    email_body +
                    """
    </tbody>
</table>

Learn more at https://app.mopub.com/ad_network_reports/
"""))


def create_logger(name, file_path):
    """
    Create log file.
    """
    logger = logging.getLogger(name)
    hdlr = logging.FileHandler(file_path)
    formatter = logging.Formatter('%(asctime)s %(levelname)s'
            ' %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)
    return logger

if __name__ == "__main__":
    """
    update_networks.py [start_day=xxxx-xx-xx] [end_day=xxxx-xx-xx]
        [email=[Y y N n]] [processes=xx]

    Updates the database from the given start date to the given end date
    sending emails if the flag is set and using the # of processes given.

    =================
    start_date, end_date:

    Date arguments must be in the folowing format:
    YEAR-MONTH-DAY
    xxxx-xx-xx

    ex. 2010-01-08

    If no arguments are given the update script runs for yesterday PST.
    (start_day and end_day are set to yesterday within the script)

    =================
    email

    Set to 'y' or 'Y' if emails should be sent.

    =================
    processes

    Processes can be any non negative integer value. The max value is the
    number of login credentials.
    """
    START_DAY = 'start_day'
    END_DAY = 'end_day'
    EMAIL = 'email'
    PROCESSES = 'processes'

    start_day = None
    end_day = None
    email = True
    processes = 1

    if (len(sys.argv) > 1):
        for arg in sys.argv[1:]:
            if START_DAY + '=' == arg[:len(START_DAY) + 1]:
                start_day = date(*[int(num) for num in arg[len(START_DAY) + 1:].split('-')])
            elif END_DAY + '=' == arg[:len(END_DAY) + 1]:
                end_day = date(*[int(num) for num in arg[len(END_DAY) + 1:].split('-')])
            elif EMAIL + '=' == arg[:len(EMAIL) + 1]:
                email = (arg[len(EMAIL) + 1:] in ('y', 'Y'))
            elif PROCESSES + '=' == arg[:len(PROCESSES) + 1]:
                processes = int(arg[len(PROCESSES) + 1:])

    setup_remote_api()
    multiprocess_update_all(start_day, end_day, email, processes)

