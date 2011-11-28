# magic import
import common.utils.test.setup

from account.models import Account, NetworkConfig
from ad_network_reports.models import *
from ad_network_reports.query_managers import AdNetworkReportQueryManager
from publisher.models import App, Site

def load_test_data():
    entities = []

    TEST_JUMPTAP_PUB_ID = 'pa_zaphrox_zaphrox_drd_app'
    TEST_ADMOB_PUB_ID = 'a14cf615dc654dd'
    TEST_IAD_PUB_ID = '329218549'
    TEST_INMOBI_PUB_ID ='4028cba630724cd90130c2adc9b6024f'
    TEST_MOBFOX_PUB_ID = 'fb8b314d6e62912617e81e0f7078b47e'

    account = Account(key_name = 'test_account')
    account.put()


    network_config = NetworkConfig(jumptap_pub_id=TEST_JUMPTAP_PUB_ID,
            admob_pub_id=TEST_ADMOB_PUB_ID, iad_pub_id=TEST_IAD_PUB_ID,
            inmobi_pub_id=TEST_INMOBI_PUB_ID,
            mobfox_pub_id=TEST_MOBFOX_PUB_ID)
    network_config.put()

    # name corresponds to jumptap login info
    app = App(account = account, name = "BET WAP Site", network_config =
            network_config)
    app.put()

    # Test adding adunit pub id for jumptap
    jumptap_adunit = Site(app_key=app)
    jumptap_adunit_config = NetworkConfig(jumptap_pub_id=
            'bet_wap_site_106andpark_top')
    jumptap_adunit_config.put()
    jumptap_adunit.network_config = jumptap_adunit_config
    jumptap_adunit.put()
    manager = AdNetworkReportQueryManager(account)

    # AdMob login info
    manager.create_login_credentials_and_mappers(ad_network_name='admob',
                                          username=
                                          'adnetwork@com2usamerica.com',
                                          password='4w47m82l5jfdqw1x',
                                          client_key=
                                          'ka820827f7daaf94826ce4cee343837a')

    # JumpTap login info
    manager.create_login_credentials_and_mappers(ad_network_name='jumptap',
                                            username='zaphrox',
                                            password='JR.7x89re0')
    # iAd login info                                  
#    iad_login_credentials = AdNetworkLoginCredentials(account=account,
#                                        ad_network_name='iad',
#                                        username='chesscom',
#                                        password='Faisal1Chess')
#    iad_login_credentials.put()

    # InMobi login info
    manager.create_login_credentials_and_mappers(ad_network_name='inmobi',
                                           username=
                                           '4028cb973099fe040130c2aa2a0904b5',
                                           password='098233019949')

    # MobFox login info
    manager.create_login_credentials_and_mappers(ad_network_name='mobfox')

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
