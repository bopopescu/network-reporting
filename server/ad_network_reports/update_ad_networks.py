import logging
import os, sys

EC2 = False

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
    sys.path.append('/Users/tiagobandeira/Documents/mopub/server')
    #sys.path.append(os.environ['PWD'])

import common.utils.test.setup

from google.appengine.api import mail

from datetime import date, timedelta

from ad_network_reports.ad_networks import AD_NETWORKS
from ad_network_reports.models import AdNetworkScrapeStats
from ad_network_reports.query_managers import AdNetworkReportQueryManager, \
        get_all_login_credentials
from common.utils import date_magic

def setup_remote_api():
    from google.appengine.ext.remote_api import remote_api_stub
    app_id = 'mopub-experimental'
    host = '38.latest.mopub-experimental.appspot.com'
    remote_api_stub.ConfigureRemoteDatastore(app_id, '/remote_api', auth_func,
            host)

def auth_func():
    return 'olp@mopub.com', 'N47935'

def send_stats_mail(manager, test_date, valid_stats_list):
    """Send email with scrape stats data for the test date organized in a
    table.
    """
    aggregate_stats = manager.roll_up_stats([stats for app_name,
        ad_network_name, stats in valid_stats_list])
    sorted(valid_stats_list, key = lambda s: s[0] + s[1])
    email_body = ""
    for app_name, ad_network_name, stats in valid_stats_list:
        email_body += ("""
        <tr>
            <td>%(app)s</td>
            <td>%(ad_network_name)s</td>
            <td>$%(revenue).2f</td>
            <td>%(attempts)d</td>
            <td>%(impressions)d</td>
            <td>%(fill_rate).2f</td>
            <td>%(clicks)d</td>
            <td>%(ctr).2f</td>
            <td>%(ecpm).2f</td>
        </tr>
        """ % dict([('app', app_name), ('ad_network_name', ad_network_name)] +
            stats.__dict__.items()))

    mail.send_mail(sender='olp@mopub.com',
                   #to='report-monitoring@mopub.com',
                   to='tiago@mopub.com',
                   subject=("Ad Network Scrape Stats for %s" %
                       test_date.strftime("%m/%d/%y")),
                   body=("Learn more at http://mopub-experimental.appspot.com/"
                         "ad_network_reports/"),
                   html=("""
<head>
    <style type="text/css">
    .total {
        font-weight:bold;}
    </style>
</head>
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
        <tr class="total">
            <td>TOTAL</td>
            <td>--</td>
            <td>$%(revenue).2f</td>
            <td>%(attempts)d</td>
            <td>%(impressions)d</td>
            <td>%(fill_rate).2f</td>
            <td>%(clicks)d</td>
            <td>%(ctr).2f</td>
            <td>%(ecpm).2f</td>
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

    if not start_date and not end_date:
        start_date = yesterday
        end_date = yesterday

    for test_date in date_magic.gen_days(start_date, end_date):

        previous_account_key = None
        valid_stats_list = []
        manager = None
        email_account = False
        # log in to ad networks and update stats for each user 
        for login_credentials in get_all_login_credentials():
            account_key = login_credentials.account.key()
            ad_network_name = login_credentials.ad_network_name
            # Only email account once for all their apps amd ad networks if they
            # want email and the information is relevant (ie. yesterdays stats)
            if email_account and (account_key != previous_account_key and
                    previous_account_key):
                # login_credentials.account.user.email
                send_stats_mail(manager, test_date, valid_stats_list)
                valid_stats_list = []
                email_account = False

            stats_list = []
            manager = AdNetworkReportQueryManager(login_credentials.account)
            # Is extra information besides the login credentials requeired for
            # the ad network? If yes append it.
            login_info = AD_NETWORKS[login_credentials.ad_network_name]. \
                    append_extra_info(login_credentials)

            try:
                scraper = AD_NETWORKS[login_credentials.ad_network_name]. \
                        constructor(login_info)

                # return a list of NetworkScrapeRecord objects of stats for
                # each app for the test_date
                stats_list = scraper.get_site_stats(test_date)
            except Exception as e:
                logging.error(("Couldn't get get stats for %s network for "
                        "\"%s\" account.  Can try again later or perhaps %s "
                        "changed it's API or site.") %
                        (login_credentials.ad_network_name, login_credentials.account.key(),
                            login_credentials.ad_network_name))
                mail.send_mail(sender='olp@mopub.com',
                               # login_credentials.account.user.email
                               to='tiago@mopub.com',
                               subject=("Ad Network Scrape Error on %s" %
                                   test_date.strftime("%m/%d/%y")),
                               body=("Couldn't get get stats for %s network "
                                   "for \"%s\" account. Error: %s" %
                                   (login_credentials.ad_network_name,
                                       login_credentials.account.key(), e)))
                raise
            #continue

            for stats in stats_list:

                # Add the current day to the db.

                publisher_id = stats.app_tag

                # Get the ad_network_app_mapper object that corresponds to the
                # login_credentials and stats.
                ad_network_app_mapper = manager.get_ad_network_app_mapper(
                        publisher_id=publisher_id,
                        login_info=login_credentials)

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
                                     dict(account = login_credentials.account.key(),
                                          pub_id = stats.app_tag,
                                          ad_network = login_credentials.
                                          ad_network_name))
                        continue
                    else:
                        logging.info("%(account)s has pub id %(pub_id)s on "
                                "%(ad_network)s that was FOUND in MoPub" %
                                     dict(account = login_credentials.account.key(),
                                          pub_id = stats.app_tag,
                                          ad_network = login_credentials.
                                          ad_network_name))
                else:
                    logging.info("%(account)s has pub id %(pub_id)s on "
                            "%(ad_network)s that\'s in MoPub" %
                            dict(account = login_credentials.account.key(),
                                pub_id = stats.app_tag,
                                ad_network = login_credentials.ad_network_name))

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
                    email_account = True
            previous_account_key = account_key

        if email_account:
            send_stats_mail(manager, test_date, valid_stats_list)

if __name__ == "__main__":
    setup_remote_api()
    update_ad_networks()

