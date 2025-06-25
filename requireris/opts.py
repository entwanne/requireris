from . import exceptions
from .account import get_accounts, add_accounts, del_accounts
from .auth import auth


def opt_get(names, db):
    accounts = get_accounts(db)
    if not names:
        names = accounts.keys()
    for name in names:
        try:
            print('%s: %s' % (name, auth(accounts[name])))
        except KeyError as e:
            raise exceptions.NameNotExist(e)

def opt_append(names, key, db):
    if not names:
        raise exceptions.NoNamesSelected
    add_accounts(names, key, db)

def opt_delete(names, db):
    if not names:
        raise exceptions.NoNamesSelected
    del_accounts(names, db)
