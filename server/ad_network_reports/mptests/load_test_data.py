# magic import
import sys
import os

sys.path.append(os.environ['PWD'])
import common.utils.test.setup

from account.models import Account, NetworkConfig
from ad_network_reports.models import *
from ad_network_reports.query_managers import AdNetworkReportManager
from publisher.models import App, Site

def load_test_data(include_iad=False):
    entities = []

    TEST_JUMPTAP_PUB_ID = 'pa_zaphrox_zaphrox_drd_app'
    TEST_ADMOB_PUB_ID = 'a14cf615dc654dd'
    TEST_IAD_PUB_ID = '329218549'
    TEST_INMOBI_PUB_ID ='4028cba630724cd90130c2adc9b6024f'
    TEST_MOBFOX_PUB_ID = 'fb8b314d6e62912617e81e0f7078b47e'

    account = Account(key_name = 'account1')
    account.put()


    network_config = NetworkConfig(account=account, jumptap_pub_id=TEST_JUMPTAP_PUB_ID,
            admob_pub_id=TEST_ADMOB_PUB_ID, inmobi_pub_id=TEST_INMOBI_PUB_ID,
            mobfox_pub_id=TEST_MOBFOX_PUB_ID)
    network_config.put()

    app = App(account=account, name="app1", network_config=
            network_config, url='http://itunes.apple.com/us/app/106-park/id'
            + TEST_IAD_PUB_ID + '?mt=8&uo=4')
    app.put()

    # Test adding adunit pub id for jumptap
    jumptap_adunit = Site(app_key=app)
    jumptap_adunit_config = NetworkConfig(account=account, jumptap_pub_id=
            'bet_wap_site_106andpark_top')
    jumptap_adunit_config.put()
    jumptap_adunit.network_config = jumptap_adunit_config
    jumptap_adunit.put()

    # AdMob login info
    AdNetworkReportManager.create_login_credentials_and_mappers(
            account=account,
            ad_network_name='admob',
            username='adnetwork@com2usamerica.com',
            password='4w47m82l5jfdqw1x',
            client_key='ka820827f7daaf94826ce4cee343837a',
            send_email=False)

    # JumpTap login info
    AdNetworkReportManager.create_login_credentials_and_mappers(
            account=account,
            ad_network_name='jumptap',
            username='zaphrox',
            password='JR.7x89re0',
            send_email=False)
    # iAd login info
    if include_iad:
        AdNetworkReportManager.create_login_credentials_and_mappers(
                account=account,
                ad_network_name='iad',
                username='chesscom',
                password='Faisal1Chess',
                send_email=False)

    # InMobi login info
    AdNetworkReportManager.create_login_credentials_and_mappers(
            account=account,
            ad_network_name='inmobi',
            username='4028cb973099fe040130c2aa2a0904b5',
            password='098233019949',
            send_email=False)

    # MobFox login info
    AdNetworkReportManager.create_login_credentials_and_mappers(
            account=account,
            ad_network_name='mobfox',
            send_email=False)

#    entities.append(AdNetworkAppMapper(application=app, ad_network_name=
#        'iad', publisher_id=TEST_IAD_PUB_ID, ad_network_login=
#        iad_login_credentials))
#    entities.append(AdNetworkAppMapper(application=app, ad_network_name=
#        'inmobi', publisher_id=TEST_INMOBI_PUB_ID, ad_network_login=
#        inmobi_login_credentials))
#    entities.append(AdNetworkAppMapper(application=app, ad_network_name=
#        'mobfox', publisher_id=TEST_MOBFOX_PUB_ID, ad_network_login=
#        mobfox_login_credentials))


    db.put(entities)
    return account

