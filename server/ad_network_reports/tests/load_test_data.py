# magic import
import common.utils.test.setup

from account.models import Account, NetworkConfig
from ad_network_reports.models import *
from ad_network_reports.query_managers import AdNetworkReportQueryManager
from publisher.models import App, Site

REAL_TEST_DATA = False

entities = []
if REAL_TEST_DATA:
    """ Office Jerk """
    officejerk_account = Account(key_name = 'office_jerk_test_account', title = 'Office Jerk')
    officejerk_account.put()

    officejerk_network_config = NetworkConfig(jumptap_pub_id = 'office_jerk_test')
    officejerk_network_config.put()

    officejerk_app = App(account = officejerk_account, name = "Office Jerk", network_config = officejerk_network_config)
    officejerk_app.put()

    # JumpTap login info
    officejerk_jumptap_login_credentials = AdNetworkLoginCredentials(account = officejerk_account, ad_network_name = 'jumptap', username = 'vrubba',
                                            password = 'fluik123!')
    officejerk_jumptap_login_credentials.put()
    entities.append(AdNetworkAppMapper(application = officejerk_app, ad_network_name = 'jumptap', publisher_id = 'office_jerk_test', ad_network_login = officejerk_jumptap_login_credentials))

    # InMobi login info
    # inmobi_login_credentials = AdNetworkLoginCredentials(account = account, ad_network_name = 'inmobi', username = 'info@fluik.com',
    #                                     password = 'fluik123!')
    # inmobi_login_credentials.put()
    # entities.append(AdNetworkAppMapper(application = app, ad_network_name = 'inmobi', publisher_id = TEST_ADMOB_PUB_ID, ad_network_login = inmobi_login_credentials))

    """ Chess.com """
    chess_account = Account(key_name = 'chess_com_test_account', title = 'Chess.com')
    chess_account.put()
    
    chess_network_config = NetworkConfig(jumptap_pub_id = 'jumptap_chess_com_test', iad_pub_id = '329218549')
    chess_network_config.put()
    
    chess_app = App(account = chess_account, name = "Chess.com - Play & Learn Chess", network_config = chess_network_config)
    chess_app.put()

    # iAd login info                                        
    chess_iad_login_credentials = AdNetworkLoginCredentials(account = chess_account, ad_network_name = 'iad', username = 'chesscom',
                                           password = 'Faisal1Chess')
    chess_iad_login_credentials.put()
    entities.append(AdNetworkAppMapper(application = chess_app, ad_network_name = 'iad', publisher_id = '329218549', ad_network_login = chess_iad_login_credentials))

    # JumpTap login info
    chess_jumptap_login_credentials = AdNetworkLoginCredentials(account = chess_account, ad_network_name = 'jumptap', username = 'chesscom',
                                            password = 'Y7u8i9o0')
    chess_jumptap_login_credentials.put()
    entities.append(AdNetworkAppMapper(application = chess_app, ad_network_name = 'jumptap', publisher_id = 'jumptap_chess_com_test', ad_network_login = chess_jumptap_login_credentials))

    # InMobi login info
    # inmobi_login_credentials = AdNetworkLoginCredentials(account = account, ad_network_name = 'inmobi', username = 'chesscom@gmail.com',
    #                                     password = 'Y7u8i9o0')
    # inmobi_login_credentials.put()

    """ Flashlight Zaphrox """
    zaphrox_account = Account(key_name = 'flashlight_zaphrox_test_account', title = 'Flashlight Zaphrox')
    zaphrox_account.put()
    
    zaphrox_network_config = NetworkConfig(jumptap_pub_id = 'flashlight_zaphrox_test')
    zaphrox_network_config.put()
    
    zaphrox_app = App(account = zaphrox_account, name = "zaphrox", network_config = zaphrox_network_config)
    zaphrox_app.put()

    # JumpTap login info
    zaphrox_jumptap_login_credentials = AdNetworkLoginCredentials(account = zaphrox_account, ad_network_name = 'jumptap', username = 'zaphrox',
                                            password = 'JR.7x89re0')
    zaphrox_jumptap_login_credentials.put()
    entities.append(AdNetworkAppMapper(application = zaphrox_app, ad_network_name = 'jumptap', publisher_id = 'flashlight_zaphrox_test', ad_network_login = zaphrox_jumptap_login_credentials))

    # InMobi login info
    # NOT WORKING
    # inmobi_login_credentials = AdNetworkLoginCredentials(account = account, ad_network_name = 'inmobi', username = 'JR.7x89re0',
    #                                     password = '1Bom.7fG8k')
    # inmobi_login_credentials.put()

    # MobFox login info
    # need the publisher id

    """ BET """
    bet_account = Account(key_name = 'bet_test_account', title = 'BET')
    bet_account.put()
    
    bet_network_config = NetworkConfig(jumptap_pub_id = 'jumptap_bet_test', admob_pub_id = 'a14c7d7e56eaff8')
    bet_network_config.put()
    
    bet_iad_network_config = NetworkConfig(iad_pub_id = '418612824')
    bet_iad_network_config.put()
       
    bet_app = App(account = bet_account, name = "BET WAP Site", network_config = bet_network_config) # Name must be the same as in Jumptap
    bet_app.put()
    
    bet_iad_app = App(account = bet_account, name = "106 & Park", network_config = bet_iad_network_config)
    bet_iad_app.put()

    # iAd login info                                        
    bet_iad_login_credentials = AdNetworkLoginCredentials(account = bet_account, ad_network_name = 'iad', username = 'betnetworks',
                                           password = 'betjames')
    bet_iad_login_credentials.put()
    entities.append(AdNetworkAppMapper(application = bet_iad_app, ad_network_name = 'iad', publisher_id = '418612824', ad_network_login = bet_iad_login_credentials))

    # AdMob login info
    bet_admob_login_credentials = AdNetworkLoginCredentials(account = bet_account, ad_network_name = 'admob', username = 'betmobilemail@gmail.com',
                                          password = 'knwyt4f5v94b61qz', client_key = 'k9417383a8224757c05fbe9aa1ef8e4c')
    bet_admob_login_credentials.put()
    entities.append(AdNetworkAppMapper(application = bet_app, ad_network_name = 'admob', publisher_id = 'a14e1c8bcb5cec6', ad_network_login = bet_admob_login_credentials))

    # JumpTap login info
    bet_jumptap_login_credentials = AdNetworkLoginCredentials(account = bet_account, ad_network_name = 'jumptap', username = 'betnetwork',
                                            password = 'BETjames')
    bet_jumptap_login_credentials.put()
    entities.append(AdNetworkAppMapper(application = bet_app, ad_network_name = 'jumptap', publisher_id = 'jumptap_bet_test', ad_network_login = bet_jumptap_login_credentials))

    """ Com2us """
    # com2us_account = Account(key_name = 'com2us_test_account', title = 'Com2us')
    # com2us_account.put()
    # 
    # com2us_app = App(account = com2us_account, name = "Slice It!", network_config = com2us_network_config)
    # com2us_app.put()
    # 
    # # JumpTap login info
    # com2us_jumptap_login_credentials = AdNetworkLoginCredentials(account = com2us_account, ad_network_name = 'jumptap', username = 'com2ususa',
                                            # password = 'zjaxntm1')
    # com2us_jumptap_login_credentials.put()

    # InMobi login info
    # inmobi_login_credentials = AdNetworkLoginCredentials(account = account, ad_network_name = 'inmobi', username = '4028cb972fe21753012ffb7680350267',
    #                                     password = '0588884947763')
    # inmobi_login_credentials.put()

    # MobFox login info
    # need the publisher id
    
    # entities.append(AdNetworkAppMapper(application = com2us_app, ad_network_name = 'jumptap', publisher_id = 'com2us_test', ad_network_login = inmobi_login_credentials))

else:
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
