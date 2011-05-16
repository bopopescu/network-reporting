from account.models import Account, User


def run():
    for account in Account.all():
        # gets or creates a django user for the google user
        django_user = User.get_djangouser_for_user(account.user)
        django_user.title   = account.title
        django_user.company = account.company
        django_user.phone   = account.phone
        django_user.country = account.country
        django_user.put()
        account.mpuser = django_user
        account.all_mpusers = [django_user.key()]
   
    # clean up Grindr   
    old_user = User.get('agltb3B1Yi1pbmNyHwsSBFVzZXIiFTEwNDg2NDM4MDAwMzExNDUwODc1Mgw')
    django_user = User.get_djangouser_for_user(old_user.user)

    account = Account.get('agltb3B1Yi1pbmNyIgsSB0FjY291bnQiFTEwMTEyNzQwOTg4Njk0NTM4Njc4NAw')
    account.all_mpusers.append(django_user.key())
    account.put()