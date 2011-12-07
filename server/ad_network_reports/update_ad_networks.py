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

from account.query_managers import AccountQueryManager
from ad_network_reports.ad_networks import AdNetwork
from ad_network_reports.models import AdNetworkAppMapper, \
        AdNetworkScrapeStats, \
        AdNetworkManagementStats
from ad_network_reports.query_managers import AdNetworkReportQueryManager, \
        get_all_login_credentials
from ad_network_reports.scrapers.unauthorized_login_exception import \
        UnauthorizedLogin
from common.utils import date_magic
from pytz import timezone

from google.appengine.ext import db

def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub
    #app_id = 'mopub-experimental'
    #host = '38.latest.mopub-experimental.appspot.com'
    app_id = 'mopub-inc'
    host = '38.latest.mopub-inc.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func,
            host)

def auth_func():
    return 'olp@mopub.com', 'N47935'

def send_stats_mail(account, manager, test_date, valid_stats_list):
    """Send email with scrape stats data for the test date organized in a
    table.
    """
    emails = ', '.join(AccountQueryManager.get_emails(account))

    if emails:
        aggregate_stats = manager.roll_up_stats([stats for app_name,
            ad_network_name, stats in valid_stats_list])
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
                <td>%(ecpm).2f</td>
            </tr>
            """ % dict([('app', app_name), ('ad_network_name', ad_network_name)]
                + stats.__dict__.items()))

        # CSS doesn't work with Gmail so use horrible html style tags ex. <b>
        mail.send_mail(sender='olp@mopub.com',
                to='tiago@mopub.com',
                #to=emails,
                #cc='tiago@mopub.com, report-monitoring@mopub.com',
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
        <th>ECPM</th>
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
            <td><b>%(ecpm).2f</b></td>
        </tr>
                    """ % aggregate_stats.__dict__ +
                    email_body +
                    """
    </tbody>
</table>
""")) #+
#"Learn more at <a href='http://mopub-experimental.appspot.com/"
#"ad_network_reports/'>MoPub</a>"))

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

    login_credentials_list = [only_these_credentials] and \
            get_all_login_credentials()

    start_date = start_date or yesterday
    end_date = end_date or yesterday

    for test_date in date_magic.gen_days(start_date, end_date):
        logging.info("TEST DATE: %s" % test_date.strftime("%Y %m %d"))
        aggregate = AdNetworkManagementStats(date=test_date)

        previous_account_key = None
        valid_stats_list = []
        login_credentials = None
        # log in to ad networks and update stats for each user
        for login_credentials in login_credentials_list:
            account_key = login_credentials.account.key()
            ad_network_name = login_credentials.ad_network_name
            # Only email account once for all their apps amd ad networks if they
            # want email and the information is relevant (ie. yesterdays stats)
            if (account_key != previous_account_key and
                    previous_account_key):
                if login_credentials.email and test_date == yesterday:
                    send_stats_mail(db.get(previous_account_key), manager,
                            test_date, valid_stats_list)
                valid_stats_list = []
            previous_account_key = account_key

            stats_list = []
            manager = AdNetworkReportQueryManager(login_credentials.account)

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
                continue
            except Exception as e:
                # This should catch ANY exception because we don't want to stop
                # updating stats if something minor breaks somewhere.
                aggregate.increment(login_credentials.ad_network_name +
                        '_login_failed')
                logging.error(("Couldn't get get stats for %s network for "
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
                aggregate.increment(login_credentials.ad_network_name +
                        '_found')

                # Add the current day to the db.

                publisher_id = stats.app_tag

                # Get the ad_network_app_mapper object that corresponds to the
                # login_credentials and stats.
                ad_network_app_mapper = manager.get_ad_network_mapper(
                        publisher_id=publisher_id,
                        ad_network_name=login_credentials.ad_network_name)

                if not ad_network_app_mapper:
                    # Check if the app has been added to MoPub prior to last
                    # update.
                    ad_network_app_mapper = manager.find_app_for_stats(
                            publisher_id, login_credentials)
                    if not ad_network_app_mapper:
                        # App is not registered in MoPub but is still in the ad
                        # network.
                        logging.info("%(account)s has pub id %(pub_id)s on "
                                "%(ad_network)s that\'s NOT in MoPub" %
                                     dict(account=login_credentials.account.
                                         key(),
                                          pub_id=stats.app_tag,
                                          ad_network=login_credentials.
                                          ad_network_name))
                        login_credentials.app_pub_ids.append(stats.app_tag)
                        login_credentials.put()
                        continue
#                        ad_network_app_mapper = AdNetworkAppMapper(
#                                ad_network_name=login_credentials.
#                                        ad_network_name,
#                                publisher_id=stats.app_tag,
#                                ad_network_login=login_credentials,
#                                application=None)
#                        ad_network_app_mapper.put()
                    else:
                        aggregate.increment(login_credentials.ad_network_name +
                                '_mapped')
                        logging.info("%(account)s has pub id %(pub_id)s on "
                                "%(ad_network)s that was FOUND in MoPub and "
                                "mapped" %
                                     dict(account = login_credentials.account.
                                         key(),
                                          pub_id = stats.app_tag,
                                          ad_network = login_credentials.
                                          ad_network_name))
                else:
                    logging.info("%(account)s has pub id %(pub_id)s on "
                            "%(ad_network)s that\'s in MoPub" %
                            dict(account = login_credentials.account.key(),
                                pub_id = stats.app_tag,
                                ad_network = login_credentials.ad_network_name))

                aggregate.increment(login_credentials.ad_network_name +
                        '_updated')
                AdNetworkScrapeStats(ad_network_app_mapper=
                        ad_network_app_mapper,
                        date=test_date,
                        revenue=float(stats.revenue),
                        attempts=stats.attempts,
                        impressions=stats.impressions,
                        fill_rate=float(stats.fill_rate),
                        clicks=stats.clicks,
                        ctr=float(stats.ctr),
                        ecpm=float(stats.ecpm)
                        ).put()

                if test_date == yesterday and login_credentials and \
                        login_credentials.email:
                    valid_stats_list.append((ad_network_app_mapper.application.
                        name, ad_network_app_mapper.ad_network_name, stats))

        aggregate.put()
        if test_date == yesterday and login_credentials and \
                login_credentials.email:
            send_stats_mail(login_credentials.account, manager, test_date,
                    valid_stats_list)

    if only_these_credentials:
        emails = ', '.join(AccountQueryManager.get_emails(
            only_these_credentials.account))
        mail.send_mail(sender='olp@mopub.com',
                       to='tiago@mopub.com',#emails,
                       subject="Finished Collecting Stats",
                       body="Check out http://frontend-0.mopub-inc." \
                               "appspot.com/ad_network_reports.")

if __name__ == "__main__":
    if(len(sys.argv) > 1):
        two_weeks_ago = date.today() - timedelta(days=14)
        update_ad_networks(start_date=two_weeks_ago,
                only_these_credentials=db.get(sys.argv[1]))
    else:
        setup_remote_api()
        update_ad_networks()

