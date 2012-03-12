from account.models import *
from account.query_managers import *

def migrate(old_email, new_email):
    user = UserQueryManager.get_by_email(old_email)
    d = user.__dict__['_entity']
    d.update({'email':new_email, 'username': new_email})
    new_user = User(**d)
    new_user.put()
    account = AccountQueryManager.get_account_for_email(old_email)
    account.mpuser = new_user
    account.all_mpusers = [new_user.key()]
    account.put()
    return account
    