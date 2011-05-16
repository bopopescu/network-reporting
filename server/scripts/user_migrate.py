from account.models import Account, User

for account in Account.all():
    # gets or creates a django user for the google user
    User.get_djangouser_for_user(account.user)
    
    