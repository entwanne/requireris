from . import exceptions
from .database import load_database, add_names, del_names
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

def opt_append(names, key, db):
    if not names:
        raise exceptions.NoNamesSelected
    add_names(names, key, db)

def opt_delete(names, db):
    if not names:
        raise exceptions.NoNamesSelected
    del_names(names, db)
