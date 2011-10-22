import logging
import os, sys

EC2 = True

if EC2:
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

from google.appengine.api import mail

from datetime import date, timedelta

from ad_network_reports.ad_networks import AD_NETWORKS
from ad_network_reports.models import AdNetworkScrapeStats
from ad_network_reports.query_managers import AdNetworkReportQueryManager, \
        get_login_credentials
from common.utils import date_magic

from google.appengine.ext import db

def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub
    app_id = 'mopub-experimental'
    host = '38.latest.mopub-experimental.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func,
            host)

def auth_func():
    return 'olp@mopub.com', 'N47935'

def send_stats_mail(account, manager, test_date, valid_stats_list):
    """Send email with scrape stats data for the test date organized in a
    table.
    """
    if account and account.user:
        emails = account.user.email()
    elif account.all_mpusers:
        emails = ', '.join([db.get(user).email for user in account.all_mpusers])

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
            """ % dict([('app', app_name), ('ad_network_name', ad_network_name)] +
                stats.__dict__.items()))

        # CSS doesn't work with Gmail so use horrible html style tags ex. <b>
        mail.send_mail(sender='olp@mopub.com',
                       #to='report-monitoring@mopub.com',
                       to='tiago@mopub.com',
                       subject=("Ad Network Scrape Stats for %s" %
                           test_date.strftime("%m/%d/%y")),
                       body=("Learn more at http://mopub-experimental.appspot.com/"
                             "ad_network_reports/"),
                       html=(emails +
                       """
<table width=100%%>
    <thead>
        <th>APP NAME</th>
        <th>AD NETWORK NAME</th>
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

def update_ad_networks(start_date = None, end_date = None):
    """Update ad network stats.

    Iterate through all AdNetworkLoginInfo. Login to the ad networks saving
    the data for the date range in the db.

    Run daily as a cron job in EC2. Email account if account wants email upon
    completion of gathering stats. Email Tiago if errors occur.
    """
    yesterday = date.today() - timedelta(days = 1)

    if start_date is None and end_date is None:
        start_date = yesterday
        end_date = yesterday

    for test_date in date_magic.gen_days(start_date, end_date):

        previous_account_key = None
        valid_stats_list = []
        email_account = False
        # log in to ad networks and update stats for each user 
        for login_info in get_login_credentials():
            account_key = login_info.account.key()
            # Only email account once for all their apps amd ad networks if they
            # want email and the information is relevant (ie. yesterdays stats)
            if (account_key != previous_account_key and
                    previous_account_key):
                if email_account:
                    send_stats_mail(db.get(previous_account_key), manager, test_date, valid_stats_list)
                valid_stats_list = []
                email_account = False

            stats_list = []
            try:
                scraper = AD_NETWORKS[login_info.ad_network_name].constructor(
                        login_info)
                # return a list of NetworkScrapeRecord objects of stats for
                # each app for the test_date
                stats_list = scraper.get_site_stats(test_date)
            except Exception as e:
                logging.error(("Couldn't get get stats for %s network for "
                        "\"%s\" account.  Can try again later or perhaps %s "
                        "changed it's API or site.") %
                        (login_info.ad_network_name, login_info.account.key(),
                            login_info.ad_network_name))
                mail.send_mail(sender='olp@mopub.com',
                               # login_info.account.user.email
                               to='tiago@mopub.com',
                               subject=("Ad Network Scrape Error on %s" %
                                   test_date.strftime("%m/%d/%y")),
                               body=("Couldn't get get stats for %s network "
                                   "for \"%s\" account. Error: %s" %
                                   (login_info.ad_network_name,
                                       login_info.account.key(), e)))
                continue

            for stats in stats_list:

                # Add the current day to the db.

                publisher_id = AD_NETWORKS[login_info.ad_network_name]. \
                        get_pub_id(stats.app_tag, login_info)

                # Get the ad_network_app_mapper object that corresponds to the
                # login_info and stats.
                manager = AdNetworkReportQueryManager(login_info.account)
                ad_network_app_mapper = manager.get_ad_network_app_mapper(
                        publisher_id=publisher_id,
                        login_info=login_info)

                if not ad_network_app_mapper:
                    # Check if the app has been added to MoPub prior to last
                    # update.
                    ad_network_app_mapper = manager.find_app_for_stats(
                            publisher_id, login_info)
                    if not ad_network_app_mapper:
                        # App is not registered in MoPub but is still in the ad
                        # network.
                        logging.info("%(account)s has pub id %(pub_id)s on "
                                "%(ad_network)s that\'s NOT in MoPub" %
                                     dict(account = login_info.account.key(),
                                          pub_id = stats.app_tag,
                                          ad_network = login_info.
                                          ad_network_name))
                        continue
                    else:
                        logging.info("%(account)s has pub id %(pub_id)s on "
                                "%(ad_network)s that was FOUND in MoPub" %
                                     dict(account = login_info.account.key(),
                                          pub_id = stats.app_tag,
                                          ad_network = login_info.
                                          ad_network_name))
                else:
                    logging.info("%(account)s has pub id %(pub_id)s on "
                            "%(ad_network)s that\'s in MoPub" %
                            dict(account = login_info.account.key(),
                                pub_id = stats.app_tag,
                                ad_network = login_info.ad_network_name))

                AdNetworkScrapeStats(ad_network_app_mapper =
                        ad_network_app_mapper,
                        date = test_date,
                        revenue = float(stats.revenue),
                        attempts = stats.attempts,
                        impressions = stats.impressions,
                        fill_rate = float(stats.fill_rate),
                        clicks = stats.clicks,
                        ctr = float(stats.ctr),
                        ecpm = float(stats.ecpm)
                        ).put()

                if test_date == yesterday:
                    valid_stats_list.append((ad_network_app_mapper.application.
                        name, ad_network_app_mapper.ad_network_name, stats))
                    if ad_network_app_mapper.send_email:
                        email_account = True
            previous_account_key = account_key

        if email_account:
            send_stats_mail(login_info.account, manager, test_date, valid_stats_list)

if __name__ == "__main__":
    setup_remote_api()
    update_ad_networks()

