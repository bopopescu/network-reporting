# Run this in the console to migrate to our new network config system

from account.models import Account, NetworkConfig

for account in Account.all():
    conf = NetworkConfig(admob_pub_id=account.admob_pub_id,
                         adsense_pub_id=account.adsense_pub_id,
                         brightroll_pub_id=account.brightroll_pub_id,
                         greystripe_pub_id=account.greystripe_pub_id,
                         inmobi_pub_id=account.inmobi_pub_id,
                         jumptap_pub_id=account.jumptap_pub_id,
                         millennial_pub_id=account.millennial_pub_id,
                         mobfox_pub_id=account.mobfox_pub_id)
    
    conf.put()
    account.network_config = conf
    account.put()
