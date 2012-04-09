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
    sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from multiprocessing import Pool
import unicodedata, re

from datetime import date, datetime, timedelta

from ad_network_reports.ad_networks import AdNetwork
from ad_network_reports.models import AdNetworkAppMapper, \
        AdNetworkScrapeStats, \
        AdNetworkManagementStats, \
        LoginStates
from ad_network_reports.query_managers import \
        IAD, \
        MOBFOX, \
        AdNetworkLoginManager, \
        AdNetworkMapperManager, \
        AdNetworkStatsManager, \
        AdNetworkAggregateManager, \
        AdNetworkManagementStatsManager
from ad_network_reports.scrapers.unauthorized_login_exception import \
        UnauthorizedLogin
from common.constants import REPORTING_NETWORKS
from common.utils import date_magic
from common.utils.connect_to_appengine import setup_remote_api
from publisher.query_managers import AppQueryManager
from pytz import timezone

# Email imports
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
# Override the default 'utf-8' email charset to avoid having the message body
# encoded in base-64 when using utf-8
import email.Charset
email.Charset.add_charset( 'utf-8', email.Charset.SHORTEST, None, None )

from google.appengine.ext import db

TESTING = False

MAX = 1000

SMTP_SERVER = 'localhost'
ADMIN_EMAIL = 'tiago@mopub.com'
SUPPORT_EMAIL = 'support@mopub.com'
REPORTING_EMAIL = 'report-monitoring@mopub.com'

def multiprocess_update_all(start_day=None,
                            end_day=None,
                            email=False,
                            processes=1,
                            testing=False):
    """
    Break up update script into multiple processes.

    Note: it works a day at a time since MobFox and Admob have a limit on the
    number of requests they can take from a given user within a window of
    time.
    """
    # Standardize the date
    pacific = timezone('US/Pacific')
    yesterday = (datetime.now(pacific) - timedelta(days=1)).date()

    # Set start and end dates
    start_day = start_day or yesterday
    end_day = end_day or yesterday

    def get_all_accounts_with_logins():
        logins_query = AdNetworkLoginManager.get_all_logins(
                order_by_account=True)
        last_account = None
        for login in logins_query:
            if login.account.key() != last_account:
                last_account = login.account.key()
                yield login.account

    days = date_magic.gen_days(start_day, end_day)

    accounts = list(get_all_accounts_with_logins())

    for day in days:
        # Create the pool of processes
        pool = Pool(processes=processes)

        results = []
        logging.info("Assigning processes in pool to collect and save stats...")
        for account in accounts:
            logging.info("Assigning process in pool to account %s and day %s" %
                    (account.key(), day))

            # Assign process in pool calling update_all and giving it it's
            # appropriate account
            email_account = email and account.ad_network_email
            results.append((account, day, pool.apply_async(update_account_stats,
                    args=(account, day, email_account, testing))))


        # Wait for all processes in pool to complete
        pool.close()
        pool.join()

        # Save management stats
        logging.info("Updating management stats...")
        stats_dict = {}
        for account, day, result in results:
            if result.successful():
                stats = result.get()
                if stats.day in stats_dict:
                    stats_dict[stats.day].combined(stats)
                else:
                    stats_dict[stats.day] = stats
            else:
                raise UpdateException(account, day)

        for stats in stats_dict.itervalues():
            stats.put_stats()

    logging.info("Finished.")


def update_account_stats(account,
                         day,
                         email,
                         testing=False):
    """
    Call update_login_stats for each login for the account for the day.

    Calculate and save roll up stats for each network and app for the account.

    Send email if account wants email.
    """
    logger_name = 'update_%s_on_%s' % (account.key(), day)
    logger = create_logger(logger_name, '/var/tmp/%s.log' % logger_name)

    try:
        management_stats = AdNetworkManagementStatsManager(day)

        all_stats = []
        aggregate_stats = []
        mappers = []
        for login in account.login_credentials:
            management_stats.increment(login.ad_network_name,
                    'attempted_logins')

            # Get mappers with stats
            mappers_with_stats = update_login_stats(login, day,
                    management_stats, logger=logger, testing=testing)

            if mappers_with_stats:
                mapper_list, stats_list = zip(*mappers_with_stats)
            else:
                mapper_list = []
                stats_list = []
            mappers += mapper_list
            all_stats += stats_list

            # Create network roll up stats
            aggregate_stats.append(AdNetworkAggregateManager.create_stats(
                login.account, day, stats_list, network=login.ad_network_name))

        # Put changes to login credentials
        db.put(account.login_credentials)

        app_stats = {}
        apps_by_key = {}
        # Update app stats
        for mapper, stats in zip(mappers, all_stats):
            key = str(mapper.application.key())
            if key in app_stats:
                app_stats[key].append(stats)
            else:
                app_stats[key] = [stats]
                apps_by_key[key] = mapper.application

        # Save all app level roll up stats to the db
        for app_key, stats_list in app_stats.iteritems():
            aggregate_stats.append(AdNetworkAggregateManager.create_stats(account,
                day, stats_list, app=apps_by_key[app_key]))

        # Save all scrape stats and aggregate (roll-up) stats for the account
        db.put(all_stats + aggregate_stats)

        # Send email
        if email:
            logging.info("Sending email to account %s" % account.key())
            send_stats_mail(account, day, zip(mappers, all_stats))
        # Return management stats
        return management_stats
    except Exception as exception:
        exc_traceback = sys.exc_info()[2]

        error_msg = "Couldn't get get stats for \"%s\" account on day %s.\n\n" \
                     "Error:\n%s\n\nTraceback:\n%s" % \
                     (account.key(), day, exception, repr(traceback.extract_tb(
                         exc_traceback)))

        # Record error in logfile
        logger.error(error_msg)

        if not testing:
            # Email admin the error
            msg = MIMEText(error_msg)
            msg['Subject'] = "Ad Network Update Error on %s" % \
                    day.strftime("%m/%d/%y")
            msg['To'] = ADMIN_EMAIL

            # Send the message via our own SMTP server, but don't include the
            # envelope header.
            s = smtplib.SMTP(SMTP_SERVER)
            s.sendmail(ADMIN_EMAIL, ADMIN_EMAIL, msg.as_string())
            s.quit()
        raise


def update_login_stats_for_check(login,
                                 start_day=None,
                                 end_day=None,
                                 testing=False):
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

    # Collect stats
    stats_list = []
    for day in date_magic.gen_days(start_day, end_day):
        stats_list += update_login_stats(login, day, update_aggregates=True,
                testing=testing)
    login.state = LoginStates.WORKING
    login.put()


    if stats_list and not testing:
        # Flush stats to db
        db.put([stats for mapper, stats in stats_list])

        # Send email informing user that they can now see statistics for the ad
        # network they just signed up for on the ad network index page.
        msg = MIMEText("Your ad network revenue report for %s is now ready. " \
                "Access it here: https://app.mopub.com/ad_network_reports.\n" \
                "\nIf you have any questions, please reach out to us at " \
                "support@mopub.com" % REPORTING_NETWORKS[login.ad_network_name])
        from_ = SUPPORT_EMAIL
        to = [] if TESTING else login.account.emails

        msg['Subject'] = "Finished Collecting Stats"
        msg['From'] = from_
        msg['To'] = ', '.join(to)

        # Send the message via our own SMTP server, but don't include the
        # envelope header.
        s = smtplib.SMTP(SMTP_SERVER)
        s.sendmail(from_, to + [ADMIN_EMAIL], msg.as_string())
        s.quit()


def retry_logins(day,
                 processes=1):
    """
    Retry failed logins for a given day.
    """
    # Create the pool of processes
    pool = Pool(processes=processes)

    management_stats = AdNetworkManagementStatsManager(day, assemble=True)
    failed_logins = management_stats.failed_logins

    logging.info("Assigning processes in pool to retry collecting stats for "
            "%s..." % day)
    results = []
    for login_key in failed_logins:
        logging.info("Assigning process in pool to login %s" % login_key)
        # Assign process in pool calling retry_login and giving it
        # it's appropriate login
        results.append((login_key, pool.apply_async(retry_login,
                args=(login_key, day))))

    logging.info("Waiting for processes to complete")
    # Wait for all processes in pool to complete
    pool.close()
    pool.join()

    # Save management stats and scrape stats in batch puts
    logging.info("Saving scrape stats...")
    all_stats = []
    total_stats = AdNetworkManagementStatsManager(day)
    for result in results:
        login_key, result = result
        if result.successful():
            stats_list, temp_stats = result.get()
            all_stats += stats_list
            total_stats.combined(temp_stats)
        else:
            logging.error("Login retry attempt failed for login key: %s" %
                    login_key)
            total_stats.append_failed_login(login_key)

    management_stats.clear_failed_logins()
    total_stats.combined(management_stats)

    # Flush stats to db
    db.put(all_stats)
    total_stats.put_stats()

    logging.info("Finished.")


def retry_login(login_key,
                day):
    # Creating logger for process
    logger_name = 'retry_%s_on_%s' % (login_key, day)
    logger = create_logger(logger_name, '/var/tmp/%s.log' % logger_name)
    try:
        login = db.get(login_key)
        # Using a different management stats for each process and combinding
        # them later keeps increments atomic
        temp_stats = AdNetworkManagementStatsManager(day)

        logger.info("Created logger and temp management stats, Calling update" \
                " login stats")
        # Return a tuple of (list of scrape stats, management stats)
        valid_stats_list = update_login_stats(login, day,
                management_stats=temp_stats, update_aggregates=True,
                logger=logger)
        result = ([stats for stats, mapper in valid_stats_list], temp_stats)
        return result
    except Exception as exception:
        exc_traceback = sys.exc_info()[2]

        error_msg = "Couldn't get get stats for \"%s\" account on day %s.\n\n" \
                     "Error:\n%s\n\nTraceback:\n%s" % \
                     (login_key, day, exception, repr(traceback.extract_tb(
                         exc_traceback)))

        # Record error in logfile
        logger.error(error_msg)
        raise


def update_login_stats(login,
                       day,
                       management_stats=None,
                       update_aggregates=False,
                       logger=None,
                       testing=False):
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
        login.state = LoginStates.ERROR
        login.put()
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

        if not testing:
            # Email admin the traceback
            msg = MIMEText("Couldn't get get stats for %s network for \"%s\" " \
                    "account. Error:\n %s\n\nTraceback:\n%s" % (login. \
                        ad_network_name, login.account.key(), e, repr(traceback. \
                            extract_tb(exc_traceback))))
            msg['Subject'] = "Ad Network Scrape Error on %s" % \
                    day.strftime("%m/%d/%y")
            msg['To'] = ADMIN_EMAIL

            # Send the message via our own SMTP server, but don't include the
            # envelope header.
            s = smtplib.SMTP(SMTP_SERVER)
            s.sendmail(ADMIN_EMAIL, ADMIN_EMAIL, msg.as_string())
            s.quit()

        login.state = LoginStates.ERROR
        login.put()
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
        mapper = mappers.get(publisher_id, None)

        if not mapper:
            if logger:
                logger.info("%(account)s has pub id %(pub_id)s on "
                        "%(network)s that\'s NOT in MoPub" %
                             dict(account=login.account.key(),
                                  pub_id=publisher_id,
                                  network=login.ad_network_name))
            login.app_pub_ids.append(publisher_id)
            continue
        else:
            if logger:
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

        if update_aggregates:
            AdNetworkAggregateManager.update_stats(login.account, mapper, day,
                    scrape_stats, network=mapper.ad_network_name)
            AdNetworkAggregateManager.update_stats(login.account, mapper, day,
                    scrape_stats, app=mapper.application)

    login.state = LoginStates.WORKING
    login.put()
    return valid_stats_list


## Helpers
#
def bulk_get(query, last_object, limit=MAX):
    return query.filter('__key__ >', last_object).fetch(limit)


def send_emails(day):
    logins_query = AdNetworkLoginManager.get_all_logins(
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
    emails = getattr(account, 'ad_network_recipients', [])

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
                   'network_name': REPORTING_NETWORKS[mapper.ad_network_name],
                   'revenue': stats.revenue,
                   'attempts': stats.attempts,
                   'impressions': stats.impressions,
                   'fill_rate': stats.fill_rate * 100,
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

        to = [] if TESTING else emails
        from_ = SUPPORT_EMAIL

        # Create message container - the correct MIME type is
        # multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Ad Network Revenue Reporting for %s" % \
                day.strftime("%m/%d/%y")
        msg['To'] = ', '.join(to)
        msg['From'] = from_
        # Create the body of the message (a plain-text and an HTML version).
        text = "Learn more at https://app.mopub.com/ad_network_reports/"
        html = ("""
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
                       'fill_rate': aggregate_stats.fill_rate * 100,
                       'clicks': aggregate_stats.clicks,
                       'ctr': aggregate_stats.ctr * 100,
                       'cpm': aggregate_stats.cpm})
        html += email_body
        html += """
            </tbody>
        </table>

        Learn more at https://app.mopub.com/ad_network_reports/
        """

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html.encode('iso-8859-15', 'replace'), 'html',
                _charset='iso-8859-15')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this
        # case the HTML message, is best and preferred.
        msg.attach(part1)
        msg.attach(part2)

        # Send the message via local SMTP server.
        s = smtplib.SMTP(SMTP_SERVER)
        # sendmail function takes 3 arguments: sender's address, recipient's
        # address and message to send - here it is sent as one string.
        s.sendmail(from_, to + [ADMIN_EMAIL] + ([] if TESTING else
            [REPORTING_EMAIL]), msg.as_string())
        s.quit()


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


class UpdateException(Exception):
    def __init__(self, account, day):
        self.account = account
        self.day = day

    def __str__(self):
        return "Unsuccessful update attempt for account %s on day %s" % \
                (self.account.key(), self.day)


class RetryException(Exception):
    def __init__(self, day):
        self.day = day

    def __str__(self):
        return "Unsuccessful retry attempt on %s" % self.day


def main(args):
    """
    update_networks.py [start_day=xxxx-xx-xx] [end_day=xxxx-xx-xx]
        [email=[Y y N n]] [processes=xx]

    Updates the database from the given start date to the given end date
    sending emails if the flag is set and using the # of processes given.

    ================
    To retry failed logins for a given day use:
    update_networks.py retry [day=xxxx-xx-xx] [processes=xx]

    =================
    start_day, end_day, day:

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

    RETRY = 'retry'
    DAY = 'day'

    start_day = None
    end_day = None
    email = False
    processes = 1

    setup_remote_api()

    def field_name_match(arg, field):
        return field + '=' == arg[:len(field) + 1]

    def parse_day(arg, field):
        return date(*[int(num) for num in arg[len(field) + 1:].split('-')])

    if (len(args) > 1):
        if RETRY == args[1]:
            for arg in args[2:]:
                if field_name_match(arg, DAY):
                    day = parse_day(arg, DAY)
                elif field_name_match(arg, PROCESSES):
                    processes = int(arg[len(PROCESSES) + 1:])
            retry_logins(day, processes)
        else:
            for arg in args[1:]:
                if HELP == arg:
                    print main.__doc__
                    return
                elif field_name_match(arg, START_DAY):
                    start_day = parse_day(arg, START_DAY)
                elif field_name_match(arg, END_DAY):
                    end_day = parse_day(arg, END_DAY)
                elif field_name_match(arg, EMAIL):
                    email = (arg[len(EMAIL) + 1:] in ('y', 'Y'))
                elif field_name_match(arg, PROCESSES):
                    processes = int(arg[len(PROCESSES) + 1:])
            multiprocess_update_all(start_day, end_day, email, processes)


if __name__ == "__main__":
    main(sys.argv)

