import re
import sys

sys.path.append('/Users/tiagobandeira/Documents/mopub/server')
import common.utils.test.setup

from google.appengine.ext import db
from account.models import Account, NetworkConfig
from publisher.models import App
from advertiser.models import AdGroup

next_key = False
app_config_list = []
app_list = []
for account in Account.all():
    valid_setup = False
    print 'account =' + str(account.key())
    for app in App.all().filter('account =', account).filter('network_config '
            '!=', None):
        print 'testing app =' + str(app.key())
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
                site = db.get(ad_group.site_keys[0])
                app = site.app_key
                ad_network = ad_network.lower()

                app_config = None
                if not app.network_config:
                    app_config = NetworkConfig()
                else:
                    app_config = app.network_config

                if hasattr(app_config, ad_network + '_pub_id'):
                    setattr(app_config, ad_network + '_pub_id',
                            getattr(n_config, ad_network + '_pub_id', None))
                    print app.name + '.' + ad_network + '_pub_id = ' +  \
                            str(getattr(n_config, ad_network + '_pub_id',
                                None))
                    app_config_list.append(app_config)
                    app.network_config = app_config
                    app_list.append(app)
    else:
        print "Account " + str(account.key()) + " has a valid setup"

#db.put(app_config_list)
#db.put(app_list)
