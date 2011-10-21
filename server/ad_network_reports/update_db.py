import re
import sys

sys.path.append('/Users/tiagobandeira/Documents/mopub/server')
import common.utils.test.setup

from google.appengine.ext import db
from account.models import Account, NetworkConfig
from publisher.models import App
from advertiser.models import AdGroup

MAX = 200
accounts = Account.all().fetch(MAX)
accounts_new = accounts
while accounts_new:
    accounts_new = Account.all().filter('__key__ >', accounts[-1]).fetch(MAX)
    accounts += accounts_new

app_config_dict = {}
for account in accounts:
    valid_setup = False
    print 'Testing account ' + str(account.key())
    for app in App.all().filter('account =', account).filter('network_config '
            '!=', None):
        if not [config for config in app.network_config.__dict__.items() if
                re.search('_pub_id', config[0]) and config[1]]:
            valid_setup = True

    if not valid_setup:
        print "Account " + str(account.key()) + " has an invalid setup"
        n_config = account.network_config
        for ad_group in AdGroup.all().filter('account =', account). \
                filter('network_type !=', None):
            if ad_group.site_keys:
                ad_network = ad_group.network_type
                print "AdGroup has an ad_network " + ad_network + \
                        " and site keys"
                for site_key in ad_group.site_keys:
                    site = db.get(site_key)
                    if site and site.app_key:
                        break

                app = None
                if site:
                    app = site.app_key

                if app:
                    ad_network = ad_network.lower()

                    app_config = app_config_dict.get(str(app.key()))
                    if not app_config:
                        app_config = app.network_config
                        if not app_config:
                            app_config = NetworkConfig()
                        app_config_dict[str(app.key())] = app_config


                    if hasattr(app_config, ad_network + '_pub_id'):
                        setattr(app_config, ad_network + '_pub_id',
                                getattr(n_config, ad_network + '_pub_id', None))
                        print app.name + '.' + ad_network + '_pub_id = ' +  \
                                str(getattr(n_config, ad_network + '_pub_id',
                                    None))
#    else:
#        print "Account " + str(account.key()) + " has a valid setup"

app_list = []
db.put(app_config_dict.values())
for app_key, app_config in app_config_dict.iteritems():
    app = db.get(app_key)
    app.network_config = app_config
    app_list.append(app)
db.put(app_list)
