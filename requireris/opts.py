from . import exceptions
from .database import load_database, save_database
from .auth import auth


def opt_get(names, db_path):
    db = load_database(db_path)
    if not names:
        names = db.keys()
    for name in names:
        try:
            print('%s: %s' % (name, auth(db[name])))
        except KeyError as e:
            raise exceptions.NameNotExist(e)


def opt_append(names, key, db_path):
    if not names:
        raise exceptions.NoNamesSelected
    if not key:
        raise exceptions.WrongKey(key)
    db = load_database(db_path)
    for name in names:
        db[name] = key
    save_database(db, db_path)


def opt_delete(names, db_path):
    if not names:
        raise exceptions.NoNameSelected
    db = load_database(db_path)
    try:
        for name in names:
            del db[name]
    except KeyError as e:
        raise exceptions.NameNotExist(e)
    save_database(db, db_path)
