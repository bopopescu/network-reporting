from account.models import Account, User
def run():
    for account in Account.all():
        if account.user:
            print account.user.email()
            if not account.mpuser:
                print 'migrating'
                django_user = User.get_djangouser_for_user(account.user)
                django_user.title   = account.title
                django_user.first_name = account.first_name
                django_user.last_name = account.last_name
                django_user.company = account.company
                django_user.phone   = account.phone
                django_user.country = account.country
                django_user.put()
                account.mpuser = django_user
                account.all_mpusers = [django_user.key()]
                account.put()
    # old_user = User.get('agltb3B1Yi1pbmNyHwsSBFVzZXIiFTEwNDg2NDM4MDAwMzExNDUwODc1Mgw')
    # django_user = User.get_djangouser_for_user(old_user.user)
    # account = Account.get('agltb3B1Yi1pbmNyIgsSB0FjY291bnQiFTEwMTEyNzQwOTg4Njk0NTM4Njc4NAw')
    # account.all_mpusers.append(django_user.key())
    # account.put()
