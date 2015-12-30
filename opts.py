from account import get_accounts, add_accounts, del_accounts
from auth import auth
import exceptions

def opt_get(users, db):
    accounts = get_accounts(db)
    if not users:
        users = accounts.keys()
    for user in users:
        try:
            print('%s: %s' % (user, auth(accounts[user])))
        except KeyError as e:
            raise exceptions.UserNotExist(e)

def opt_append(users, key, db):
    if not users:
        raise exceptions.NoUsersSelected
    add_accounts(users, key, db)

def opt_delete(users, db):
    if not users:
        raise exceptions.NoUsersSelected
    del_accounts(users, db)
