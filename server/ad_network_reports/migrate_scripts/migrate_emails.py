from ad_network_reports.query_managers import AdNetworkLoginCredentialsManager
from google.appengine.ext import db

logins = AdNetworkLoginCredentialsManager.get_all_logins(
        order_by_account=True).fetch(1000)
last_account = None
accounts= []
for login in logins:
    if login.account.key() != last_account:
        last_account = login.account.key()
        if login.email:
            account = login.account
            account.ad_network_email = True
            account.ad_network_recipients = list(account.emails)
            print "Updating account"
            print str(account.key())
            print account.emails
            print
            accounts.append(login.account)
db.put(accounts)

