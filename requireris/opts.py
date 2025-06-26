from . import exceptions
from .auth import auth


def opt_get(db, *names):
    if not names:
        names = db.keys()
    for name in names:
        try:
            print('%s: %s' % (name, auth(db[name])))
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
