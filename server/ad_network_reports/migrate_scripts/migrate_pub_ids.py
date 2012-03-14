import re
import sys
import os

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from google.appengine.ext import db
from account.models import Account, NetworkConfig
from publisher.models import App
from advertiser.models import AdGroup

MAX = 200

def update():
    accounts = Account.all().fetch(MAX)
    accounts_new = accounts
    while accounts_new:
        accounts_new = Account.all().filter('__key__ >', accounts[-1]).fetch(MAX)
        accounts += accounts_new
    length = len(accounts)

    app_config_dict = {}
    for index, account in enumerate(accounts):
        valid_setup = False
        print '%d/%d testing account: %s' % (index, length, str(account.key()))
        for app in App.all().filter('account =', account).filter('network_config '
                '!=', None):
            # Are pub ids set at the app level?
            if [config for config in app.network_config.__dict__.items() if
                    re.search('_pub_id', config[0]) and config[1]]:
                valid_setup = True
                break

        if not valid_setup:
            print "Account " + str(account.key()) + " has an INVALID setup"
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
                            print "could not find app_config in dict"
                            app_config = app.network_config
                            if not app_config:
                                print "creating app_config"
                                app_config = NetworkConfig()
                            app_config_dict[str(app.key())] = app_config


                        #if hasattr(app_config, ad_network + '_pub_id'):
                        setattr(app_config, ad_network + '_pub_id',
                                getattr(n_config, ad_network + '_pub_id', None))
                        print app.name + '.' + ad_network + '_pub_id = ' +  \
                                str(getattr(n_config, ad_network + '_pub_id',
                                    None))
#        else:
#            print "Account " + str(account.key()) + " has a valid setup"

    app_list = []
    db.put(app_config_dict.values())
    print "Put %d app_configs in dict into the db" % len(app_config_dict)
    for app_key, app_config in app_config_dict.iteritems():
        app = db.get(app_key)
        app.network_config = app_config
        app_list.append(app)
    db.put(app_list)

def update_account(account):
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

                app_config = app.network_config
                if not app_config:
                    print "creating app_config"
                    app_config = NetworkConfig()

                setattr(app_config, ad_network + '_pub_id',
                        getattr(n_config, ad_network + '_pub_id', None))
                print app.name + '.' + ad_network + '_pub_id = ' +  \
                        str(getattr(n_config, ad_network + '_pub_id',
                            None))

                app_config.put()
                app.network_config = app_config
                app.put()
