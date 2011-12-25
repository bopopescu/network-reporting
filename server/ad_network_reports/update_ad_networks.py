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

from google.appengine.api import mail

from datetime import date, datetime, timedelta

from ad_network_reports.ad_networks import AdNetwork
from ad_network_reports.models import AdNetworkAppMapper, \
        AdNetworkScrapeStats, \
        AdNetworkManagementStats
from ad_network_reports.query_managers import \
        AD_NETWORK_NAMES, \
        IAD, \
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

def send_stats_mail(account, test_date, valid_stats_list):
    """Send email with scrape stats data for the test date organized in a
    table.
    """
    emails = ', '.join(account.emails)

    if emails and valid_stats_list:
        aggregate_stats = AdNetworkStatsManager.roll_up_stats([stats for
            app_name, ad_network_name, stats in valid_stats_list])
        valid_stats_list = sorted(valid_stats_list, key = lambda s: s[0] + s[1])
        email_body = ""
        for app_name, ad_network_name, stats in valid_stats_list:
            email_body += ("""
            <tr>
                <td>%(app)s</td>
                <td>%(ad_network_name)s</td>
                <td>$%(revenue).2f</td>
                <td>%(attempts)d</td>
                <td>%(impressions)d</td>
                <td>%(fill_rate).2f%%</td>
                <td>%(clicks)d</td>
                <td>%(ctr).2f%%</td>
                <td>%(cpm).2f</td>
            </tr>
            """ % {'app': app_name,
                   'ad_network_name': ad_network_name,
                   'revenue': stats.revenue,
                   'attempts': stats.attempts,
                   'impressions': stats.impressions,
                   'fill_rate': stats.fill_rate,
                   'clicks': stats.clicks,
                   'ctr': stats.ctr * 100,
                   'cpm': stats.cpm})

        # CSS doesn't work with Gmail so use horrible html style tags ex. <b>
        mail.send_mail(sender='olp@mopub.com',
                reply_to='support@mopub.com',
                to='tiago@mopub.com' if TESTING else emails,
                bcc='tiago@mopub.com' if TESTING else
                    'tiago@mopub.com, report-monitoring@mopub.com',
                subject=("Ad Network Revenue Reporting for %s" %
                                test_date.strftime("%m/%d/%y")),
                body=("Learn more at http://mopub-experimental.appspot."
                    "com/ad_network_reports/"),
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
"""))

def update_ad_networks(start_date=None, end_date=None, only_these_credentials=
        None):
    """Update ad network stats.

    Iterate through all AdNetworkLoginCredentials. Login to the ad networks
    saving the data for the date range in the db.

    Run daily as a cron job in EC2. Email account if account wants email upon
    completion of gathering stats. Email Tiago if errors occur.
    """
    # Standardize the date (required since something messes with it)
    pacific = timezone('US/Pacific')
    yesterday = (datetime.now(pacific) - timedelta(days=1)).date()

    login_credentials_list = (only_these_credentials,) if \
            only_these_credentials else AdNetworkLoginCredentialsManager. \
            get_all_login_credentials()

    # Create log file.
    if not only_these_credentials:
        logger = logging.getLogger('update_log')
        hdlr = logging.FileHandler('/var/tmp/update.log')
    else:
        logger = logging.getLogger('update_log_' +
                str(only_these_credentials.key()))
        hdlr = logging.FileHandler('/var/tmp/check_%s.log' %
                str(only_these_credentials.key()))
    formatter = logging.Formatter('%(asctime)s %(levelname)s'
            ' %(message)s')
    hdlr.setFormatter(formatter)
    logger.addHandler(hdlr)
    logger.setLevel(logging.DEBUG)

    start_date = start_date or yesterday
    end_date = end_date or yesterday

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

            account_key = login_credentials.account.key()
            ad_network_name = login_credentials.ad_network_name
            # Only email account once for all their apps amd ad networks if they
            # want email and the information is relevant (ie. yesterdays stats)
            if (account_key != previous_account_key and
                    previous_account_key):
                if login_credentials.email and test_date == yesterday:
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

                if not only_these_credentials:
                    aggregate.increment(login_credentials.ad_network_name,
                            'updated')
                scrape_stats = AdNetworkScrapeStats(ad_network_app_mapper=
                    ad_network_app_mapper,
                    date=test_date,
                    revenue=float(stats.revenue),
                    attempts=stats.attempts,
                    impressions=stats.impressions,
                    clicks=stats.clicks)
                scrape_stats.put()

                if test_date == yesterday and login_credentials and \
                        login_credentials.email:
                    valid_stats_list.append((ad_network_app_mapper.application.
                        name, ad_network_app_mapper.ad_network_name,
                        scrape_stats))
            login_credentials.put()

    if not only_these_credentials:
        aggregate.put_stats()
        if test_date == yesterday and login_credentials and \
                login_credentials.email:
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

if __name__ == "__main__":
    setup_remote_api()
    update_ad_networks()

