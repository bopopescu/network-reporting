# magic import
import common.utils.test.setup

from account.models import Account, NetworkConfig
from network_scraping.models import *
from publisher.models import App

REAL_TEST_DATA = True

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
    officejerk_jumptap_login_info = AdNetworkLoginInfo(account = officejerk_account, ad_network_name = 'jumptap', username = 'vrubba',
                                            password = 'fluik123!')
    officejerk_jumptap_login_info.put()
    entities.append(AdNetworkAppMapper(application = officejerk_app, ad_network_name = 'jumptap', publisher_id = 'office_jerk_test', ad_network_login = officejerk_jumptap_login_info, send_email = True))

    # InMobi login info
    # inmobi_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'inmobi', username = 'info@fluik.com',
    #                                     password = 'fluik123!')
    # inmobi_login_info.put()
    # entities.append(AdNetworkAppMapper(application = app, ad_network_name = 'inmobi', publisher_id = TEST_ADMOB_PUB_ID, ad_network_login = inmobi_login_info))

    """ Chess.com """
    chess_account = Account(key_name = 'chess_com_test_account', title = 'Chess.com')
    chess_account.put()
    
    chess_network_config = NetworkConfig(jumptap_pub_id = 'jumptap_chess_com_test', iad_pub_id = '329218549')
    chess_network_config.put()
    
    chess_app = App(account = chess_account, name = "Chess.com - Play & Learn Chess", network_config = chess_network_config)
    chess_app.put()

    # iAd login info                                        
    chess_iad_login_info = AdNetworkLoginInfo(account = chess_account, ad_network_name = 'iad', username = 'chesscom',
                                           password = 'Faisal1Chess')
    chess_iad_login_info.put()
    entities.append(AdNetworkAppMapper(application = chess_app, ad_network_name = 'iad', publisher_id = '329218549', ad_network_login = chess_iad_login_info, send_email = True))

    # JumpTap login info
    chess_jumptap_login_info = AdNetworkLoginInfo(account = chess_account, ad_network_name = 'jumptap', username = 'chesscom',
                                            password = 'Y7u8i9o0')
    chess_jumptap_login_info.put()
    entities.append(AdNetworkAppMapper(application = chess_app, ad_network_name = 'jumptap', publisher_id = 'jumptap_chess_com_test', ad_network_login = chess_jumptap_login_info, send_email = True))

    # InMobi login info
    # inmobi_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'inmobi', username = 'chesscom@gmail.com',
    #                                     password = 'Y7u8i9o0')
    # inmobi_login_info.put()

    """ Flashlight Zaphrox """
    zaphrox_account = Account(key_name = 'flashlight_zaphrox_test_account', title = 'Flashlight Zaphrox')
    zaphrox_account.put()
    
    zaphrox_network_config = NetworkConfig(jumptap_pub_id = 'flashlight_zaphrox_test')
    zaphrox_network_config.put()
    
    zaphrox_app = App(account = zaphrox_account, name = "zaphrox", network_config = zaphrox_network_config)
    zaphrox_app.put()

    # JumpTap login info
    zaphrox_jumptap_login_info = AdNetworkLoginInfo(account = zaphrox_account, ad_network_name = 'jumptap', username = 'zaphrox',
                                            password = 'JR.7x89re0')
    zaphrox_jumptap_login_info.put()
    entities.append(AdNetworkAppMapper(application = zaphrox_app, ad_network_name = 'jumptap', publisher_id = 'flashlight_zaphrox_test', ad_network_login = zaphrox_jumptap_login_info, send_email = True))

    # InMobi login info
    # NOT WORKING
    # inmobi_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'inmobi', username = 'JR.7x89re0',
    #                                     password = '1Bom.7fG8k')
    # inmobi_login_info.put()

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
    bet_iad_login_info = AdNetworkLoginInfo(account = bet_account, ad_network_name = 'iad', username = 'betnetworks',
                                           password = 'betjames')
    bet_iad_login_info.put()
    entities.append(AdNetworkAppMapper(application = bet_iad_app, ad_network_name = 'iad', publisher_id = '418612824', ad_network_login = bet_iad_login_info, send_email = True))

    # AdMob login info
    bet_admob_login_info = AdNetworkLoginInfo(account = bet_account, ad_network_name = 'admob', username = 'betmobilemail@gmail.com',
                                          password = 'knwyt4f5v94b61qz', client_key = 'k9417383a8224757c05fbe9aa1ef8e4c')
    bet_admob_login_info.put()
    entities.append(AdNetworkAppMapper(application = bet_app, ad_network_name = 'admob', publisher_id = 'a14e1c8bcb5cec6', ad_network_login = bet_admob_login_info, send_email = True))

    # JumpTap login info
    bet_jumptap_login_info = AdNetworkLoginInfo(account = bet_account, ad_network_name = 'jumptap', username = 'betnetwork',
                                            password = 'BETjames')
    bet_jumptap_login_info.put()
    entities.append(AdNetworkAppMapper(application = bet_app, ad_network_name = 'jumptap', publisher_id = 'jumptap_bet_test', ad_network_login = bet_jumptap_login_info, send_email = True))

    # """ Com2us """
    # com2us_account = Account(key_name = 'com2us_test_account', title = 'Com2us')
    # com2us_account.put()
    # 
    # com2us_network_config = NetworkConfig(jumptap_pub_id = 'com2us_test')
    # com2us_network_config.put()
    # 
    # com2us_app = App(account = com2us_account, name = "Slice It!", network_config = com2us_network_config)
    # com2us_app.put()
    # 
    # # JumpTap login info
    # com2us_jumptap_login_info = AdNetworkLoginInfo(account = com2us_account, ad_network_name = 'jumptap', username = 'com2ususa',
    #                                         password = 'zjaxntm1')
    # com2us_jumptap_login_info.put()
    # entities.append(AdNetworkAppMapper(application = com2us_app, ad_network_name = 'jumptap', publisher_id = 'com2us_test', ad_network_login = com2us_jumptap_login_info, send_email = True))

    # InMobi login info
    # inmobi_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'inmobi', username = 'adnetwork@com2usamerica.com',
    #                                     password = 'zjaxntm1')
    # inmobi_login_info.put()

    # MobFox login info
    # need the publisher id

else:
    TEST_JUMPTAP_PUB_ID = 'test' # Needed in network config
    TEST_ADMOB_PUB_ID = 'a14a9ed9bf1fdcd'
    TEST_IAD_PUB_ID = '329218549'
    TEST_INMOBI_PUB_ID ='4028cb962b75ff06012b792fc5fb0045'
    TEST_MOBFOX_PUB_ID = 'fb8b314d6e62912617e81e0f7078b47e'

    account = Account()
    account.put()

    # AdMob login info
    admob_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'admob', username = 'njamal@stanford.edu',
                                          password = 'xckjhfn3xprkxksm', client_key = 'k907a03ee39cecb699b5ad45c5eded01')
    admob_login_info.put()

    # JumpTap login info
    jumptap_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'jumptap', username = 'vrubba',
                                            password = 'fluik123!')
    jumptap_login_info.put()

    # iAd login info                                  
    iad_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'iad', username = 'chesscom',
                                           password = 'Faisal1Chess')
    iad_login_info.put()

    # InMobi login info
    inmobi_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'inmobi', username = '4028cb8b2b617f70012b792fe65e00a2',
                                        password = '84585161')
    inmobi_login_info.put()

    # MobFox login info
    mobfox_login_info = AdNetworkLoginInfo(account = account, ad_network_name = 'mobfox', publisher_ids = ['fb8b314d6e62912617e81e0f7078b47e'])
    mobfox_login_info.put()

    # Only needed for jumptap
    office_jerk_network_config = NetworkConfig(jumptap_pub_id = TEST_JUMPTAP_PUB_ID)
    office_jerk_network_config.put()

    # name corresponds to jumptap login info
    office_jerk_app = App(account = account, name = "Office Jerk", network_config = office_jerk_network_config)
    office_jerk_app.put()

    entities.append(AdNetworkAppMapper(application = office_jerk_app, ad_network_name = 'admob', publisher_id = TEST_ADMOB_PUB_ID, ad_network_login = admob_login_info))
    entities.append(AdNetworkAppMapper(application = office_jerk_app, ad_network_name = 'jumptap', publisher_id = TEST_JUMPTAP_PUB_ID, ad_network_login = jumptap_login_info, send_email = True))
    entities.append(AdNetworkAppMapper(application = office_jerk_app, ad_network_name = 'iad', publisher_id = TEST_IAD_PUB_ID, ad_network_login = iad_login_info))
    entities.append(AdNetworkAppMapper(application = office_jerk_app, ad_network_name = 'inmobi', publisher_id = TEST_INMOBI_PUB_ID, ad_network_login = inmobi_login_info))
    entities.append(AdNetworkAppMapper(application = office_jerk_app, ad_network_name = 'mobfox', publisher_id = TEST_MOBFOX_PUB_ID, ad_network_login = mobfox_login_info))

    
db.put(entities)


