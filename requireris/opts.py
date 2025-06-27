from fnmatch import fnmatch

from . import exceptions
from .totp import generate_totp


def opt_list(db, *patterns):
    print('Available keys:')
    for name in db.keys():
        if not patterns or any(fnmatch(name, p) for p in patterns):
            print(name)


def opt_get(db, *names):
    if not names:
        raise exceptions.NoNameSelected
    for name in names:
        try:
            print('%s: %s' % (name, generate_totp(db[name])))
        except KeyError as e:
            raise exceptions.NameNotExist(e)


def opt_append(db, name, key):
    if not key:
        raise exceptions.WrongKey(key)
    db[name] = key
    db.save()


def opt_delete(db, *names):
    if not names:
        raise exceptions.NoNameSelected
    try:
        for name in names:
            del db[name]
    except KeyError as e:
        raise exceptions.NameNotExist(e)
    db.save()
