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
        AdNetworkLoginManager, \
        AdNetworkMapperManager, \
        AdNetworkStatsManager, \
        AdNetworkAggregateManager, \
        AdNetworkManagementStatsManager
from ad_network_reports.scrapers.unauthorized_login_exception import \
        UnauthorizedLogin
from common.utils import date_magic
from common.utils.connect_to_appengine import setup_remote_api
from publisher.query_managers import AppQueryManager
from pytz import timezone

from google.appengine.ext import db

TESTING = False

MAX = 1000
BUFFER = 200


# TODO: Implement pool of processes that handles the update by day and login
# TODO: Keep stats buffered in memory for emails to prevent seperate queries
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

    logging.info("Creating processes to collect and save stats...")
    children = []
    offset_adjustment = 0
    for num in range(processes):
        # Create a log file
        info = (num,
                start_day.strftime('%Y_%m_%d'),
                end_day.strftime('%Y_%m_%d'),)
        logger = create_logger('update_p%d_%s_to_%s_log' % info,
                '/var/tmp/update_p%d_%s_to_%s.log' % info)

        # Calculate offset
        offset = range_ * num + offset_adjustment

        adjusted_range = range_
        # Add one to range of each process until remainder = 0
        if remainder > 0:
            adjusted_range += 1
            offset_adjustment += 1
            remainder -= 1

        logger.info("Starting process %d with offset %d and range %d" % (num,
            offset, adjusted_range))

        # Spawn off new process calling update_all and giving it it's
        # appropriate offset (start point) and range
        process = Process(target=update_all,
                kwargs={'start_day': start_day,
                        'end_day': end_day,
                        'logger': logger,
                        'offset': offset,
                        'range_': adjusted_range,
                        'queue': queue})
        process.start()
        children.append(process)

    # Wait for all processes to complete
    for process in children:
        process.join()

    logging.info("Updating management stats...")
    # Save management stats
    stats_dict = {}
    while not queue.empty():
        logging.info("Pop from queue")
        stats = queue.get()
        if stats.day in stats_dict:
            logging.info("Combineding")
            stats_dict[stats.day].combined(stats)
        else:
            logging.info("Creating")
            stats_dict[stats.day] = stats

    for stats in stats_dict.itervalues():
        logging.info("Putting stats")
        stats.put_stats()

    logging.info("Emailing accounts...")
    # Email accounts
    if email:
        for day in date_magic.gen_days(start_day, end_day):
            send_emails(day)

    logging.info("Finished.")


def update_all(start_day=None, end_day=None, logger=None, offset=0, range_=-1,
        queue=None):
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

    # Set start and end dates
    start_day = start_day or yesterday
    end_day = end_day or yesterday

    stats_list = []
    # Iterate through date range
    for day in date_magic.gen_days(start_day, end_day):
        logins_query = AdNetworkLoginCredentialsManager.get_all_logins()
        limit = min(range_, MAX)
        count = limit
        logins = logins_query.fetch(limit, offset=offset)

        if logger:
            logger.info("TEST DATE: %s" % day.strftime("%Y %m %d"))
        # Create Management Stats
        management_stats = AdNetworkManagementStatsManager(day=day)

        while logins:
            # Iterate through logins
            for login in logins:
                stats_list += update_login_stats(login, day, management_stats,
                        logger, queue)

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


        if queue and management_stats:
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


def update_login_stats(login, day, management_stats=None, logger=None,
        queue=None):
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

    # Get all mappers for login and put them in a dict for quick access
    mappers = {}
    for mapper in AdNetworkMapperManager.get_mappers_by_login(
            login).fetch(MAX):
        mappers[mapper.publisher_id] = mapper

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

        # Get the mapper object that corresponds to the login and stats.
#        mapper = AdNetworkMapperManager.get_mapper(publisher_id=publisher_id,
#                ad_network_name=login.ad_network_name)
        mapper = mappers.get(publisher_id, None)

        if not mapper:
#            # Check if the app has been added to MoPub prior to last
#            # update.
#            mapper = AdNetworkMapperManager. \
#                    find_app_for_stats(publisher_id, login)
#            if not mapper:
#                # App is not registered in MoPub but is still in the ad
#                # network.
            if logger:
                logger.info("%(account)s has pub id %(pub_id)s on "
                        "%(network)s that\'s NOT in MoPub" %
                             dict(account=login.account.key(),
                                  pub_id=publisher_id,
                                  network=login.ad_network_name))
            login.app_pub_ids.append(publisher_id)
            continue
#            else:
#                if management_stats:
#                    management_stats.increment(login.ad_network_name, 'mapped')
#                if logger:
#                    logger.info("%(account)s has pub id %(pub_id)s on "
#                            "%(network)s that was FOUND in MoPub and "
#                            "mapped" %
#                                 dict(account=login.account.
#                                     key(),
#                                      pub_id=publisher_id,
#                                      network=login.ad_network_name))
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
    logins_query = AdNetworkLoginCredentialsManager.get_all_logins(
            order_by_account=True)

    last_account = None
    for login in logins_query:
        if login.account.key() != last_account:
            last_account = login.account.key()
            if login.account.ad_network_email:
                mappers = AdNetworkMapperManager.get_mappers(login.account)
                stats_list = [(mapper, AdNetworkStatsManager. \
                        get_stats_for_mapper_and_days(mapper, (day,))[0]) for
                        mapper in mappers]
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
    emails = ', '.join(getattr(account, 'ad_network_recipients', []))

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

# TODO: Save aggregate stats with multiprocessing
"""
def update_ad_networks(start_date=None, end_date=None, only_these_credentials=
        None):

    for test_date in date_magic.gen_days(start_date, end_date):
        logger.info("TEST DATE: %s" % test_date.strftime("%Y %m %d"))
        if not only_these_credentials:
            aggregate = AdNetworkManagementStatsManager(day=test_date)

        previous_account_key = None
        valid_stats_list = []
        login_credentials = None
        # log in to ad networks and update stats for each user
        for login_credentials in login_credentials_list:
            login_credentials.app_pub_ids = []
            if not only_these_credentials:
                aggregate.increment(login_credentials.ad_network_name,
                        'attempted_logins')

            account_key = login_credentials.account.key()
            ad_network_name = login_credentials.ad_network_name
            # Only email account once for all their apps amd ad networks if they
            # want email and the information is relevant (ie. yesterdays stats)
            if (account_key != previous_account_key and
                    previous_account_key):
                if login_credentials.email:
                    send_stats_mail(db.get(previous_account_key), test_date,
                            valid_stats_list)
                valid_stats_list = []
            previous_account_key = account_key

            stats_list = []
            try:
                # AdNetwork is a factory class that returns the appropriate
                # subclass of itself when created.
                ad_network = AdNetwork(login_credentials)

                ad_network.append_extra_info()
                scraper = ad_network.create_scraper()

                # Return a list of NetworkScrapeRecord objects of stats for
                # each app for the test_date
                stats_list = scraper.get_site_stats(test_date)
            except UnauthorizedLogin:
                # TODO: Send user email that we can't get their stats
                # because their login doesn't work. (Most likely they changed
                # it since we last verified)
                logger.info("Unauthorized login attempted by account:%s on %s."
                        % (login_credentials.account,
                            login_credentials.ad_network_name))
                continue
            except Exception as e:
                # This should catch ANY exception because we don't want to stop
                # updating stats if something minor breaks somewhere.
                if not only_these_credentials:
                    aggregate.append_failed_login(login_credentials)
                logger.error(("Couldn't get get stats for %s network for "
                        "\"%s\" account.  Can try again later or perhaps %s "
                        "changed it's API or site.") %
                        (login_credentials.ad_network_name,
                            login_credentials.account.key(),
                            login_credentials.ad_network_name))
                exc_traceback = sys.exc_info()[2]
                mail.send_mail(sender='olp@mopub.com',
                               to='tiago@mopub.com',
                               subject=("Ad Network Scrape Error on %s" %
                                   test_date.strftime("%m/%d/%y")),
                               body=("Couldn't get get stats for %s network "
                                   "for \"%s\" account. Error:\n %s\n\n"
                                   "Traceback:\n%s" % (login_credentials.
                                       ad_network_name, login_credentials.
                                       account.key(), e, repr(traceback.
                                           extract_tb(exc_traceback)))))
                continue

            for stats in stats_list:
                if not only_these_credentials:
                    aggregate.increment(login_credentials.ad_network_name,
                            'found')

                # Add the current day to the db.
                if login_credentials.ad_network_name == IAD:
                    publisher_id = AppQueryManager.get_iad_pub_id(
                            login_credentials.account, stats.app_tag)
                else:
                    publisher_id = stats.app_tag

                if not publisher_id:
                    login_credentials.app_pub_ids.append(stats.app_tag)
                    continue

                # Get the ad_network_app_mapper object that corresponds to the
                # login_credentials and stats.
                ad_network_app_mapper = AdNetworkMapperManager. \
                        get_ad_network_mapper(publisher_id=publisher_id,
                                ad_network_name=login_credentials.
                                    ad_network_name)

                if not ad_network_app_mapper:
                    # Check if the app has been added to MoPub prior to last
                    # update.
                    ad_network_app_mapper = AdNetworkMapperManager. \
                            find_app_for_stats(publisher_id, login_credentials)
                    if not ad_network_app_mapper:
                        # App is not registered in MoPub but is still in the ad
                        # network.
                        logger.info("%(account)s has pub id %(pub_id)s on "
                                "%(ad_network)s that\'s NOT in MoPub" %
                                     dict(account=login_credentials.account.
                                         key(),
                                          pub_id=publisher_id,
                                          ad_network=login_credentials.
                                          ad_network_name))
                        login_credentials.app_pub_ids.append(publisher_id)
                        continue
                    else:
                        if not only_these_credentials:
                            aggregate.increment(login_credentials.
                                    ad_network_name, 'mapped')
                        logger.info("%(account)s has pub id %(pub_id)s on "
                                "%(ad_network)s that was FOUND in MoPub and "
                                "mapped" %
                                     dict(account=login_credentials.account.
                                         key(),
                                          pub_id=publisher_id,
                                          ad_network=login_credentials.
                                          ad_network_name))
                else:
                    logger.info("%(account)s has pub id %(pub_id)s on "
                            "%(ad_network)s that\'s in MoPub" %
                            dict(account=login_credentials.account.key(),
                                pub_id=publisher_id,
                                ad_network=login_credentials.ad_network_name))

                scrape_stats = AdNetworkScrapeStats(ad_network_app_mapper=
                    ad_network_app_mapper,
                    date=test_date,
                    revenue=float(stats.revenue),
                    attempts=stats.attempts,
                    impressions=stats.impressions,
                    clicks=stats.clicks)

                if only_these_credentials:
                    # Update the rolled up stats.
                    AdNetworkAggregateManager.update_stats(login_credentials. \
                            account, ad_network_app_mapper, test_date, scrape_stats,
                            network=ad_network_app_mapper.ad_network_name)
                    AdNetworkAggregateManager.update_stats(login_credentials. \
                            account, ad_network_app_mapper, test_date, scrape_stats,
                            app=ad_network_app_mapper.application)
                else:
                    # Calculate the app roll-up and store it in the db.
                    # TODO: could be faster if we didn't store it until we
                    # finished with the account
                    AdNetworkAggregateManager.put_stats(login_credentials. \
                            account, test_date, [scrape_stats],
                            app=ad_network_app_mapper.application)
                    aggregate.increment(login_credentials.ad_network_name,
                            'updated')
                scrape_stats.put()

                if not only_these_credentials and login_credentials and \
                        login_credentials.email:
                    valid_stats_list.append((ad_network_app_mapper,
                        scrape_stats))
            if not only_these_credentials:
                # Calculate the network roll-up and store it in the db.
                AdNetworkAggregateManager.put_stats(login_credentials.account,
                        test_date, stats_list,
                        network=login_credentials.ad_network_name)

            login_credentials.put()

    if not only_these_credentials:
        aggregate.put_stats()
        if login_credentials and login_credentials.email:
            send_stats_mail(login_credentials.account, test_date,
                    valid_stats_list)
    elif stats_list:
        emails = ', '.join(db.get(account_key).emails)
        mail.send_mail(sender='olp@mopub.com',
                       reply_to='support@mopub.com',
                       to='tiago@mopub.com' if TESTING else emails,
                       bcc='tiago@mopub.com',
                       subject="Finished Collecting Stats",
                       body="Your ad network revenue report for %s is now ready. " \
                               "Access it here: https://app.mopub.com/ad_network_reports.\n\n" \
                               "If you have any questions, please reach out to us at support@mopub.com" \
                               % AD_NETWORK_NAMES[only_these_credentials.ad_network_name])
=======
"""

def main(args):
    """
    update_networks.py [start_day=xxxx-xx-xx] [end_day=xxxx-xx-xx]
        [email=[Y y N n]] [processes=xx]

    Updates the database from the given start date to the given end date
    sending emails if the flag is set and using the # of processes given.

    =================
    start_day, end_day:

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
    HELP = 'help'
    START_DAY = 'start_day'
    END_DAY = 'end_day'
    EMAIL = 'email'
    PROCESSES = 'processes'

    start_day = None
    end_day = None
    email = True
    processes = 1

    if (len(args) > 1):
        for arg in args[1:]:
            if HELP == arg:
                print main.__doc__
                return
            if START_DAY + '=' == arg[:len(START_DAY) + 1]:
                start_day = date(*[int(num) for num in arg[len(START_DAY) +
                    1:].split('-')])
            elif END_DAY + '=' == arg[:len(END_DAY) + 1]:
                end_day = date(*[int(num) for num in arg[len(END_DAY) +
                    1:].split('-')])
            elif EMAIL + '=' == arg[:len(EMAIL) + 1]:
                email = (arg[len(EMAIL) + 1:] in ('y', 'Y'))
            elif PROCESSES + '=' == arg[:len(PROCESSES) + 1]:
                processes = int(arg[len(PROCESSES) + 1:])

    setup_remote_api()
    multiprocess_update_all(start_day, end_day, email, processes)

if __name__ == "__main__":
    main(sys.argv)
