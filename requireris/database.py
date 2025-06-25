from configparser import ConfigParser, UNNAMED_SECTION
from base64 import b32decode

from . import exceptions


class Database:
    def __init__(self, **data):
        self._data = data

    @classmethod
    def load(cls, file):
        config = ConfigParser(allow_unnamed_section=True)
        config.read_file(file)

        if not config.has_section(UNNAMED_SECTION):
            return cls()

        values = config[UNNAMED_SECTION]
        return cls(**{
            name: key.replace(' ', '').upper()
            for name, key in values.items()
        })

    def dump(self, file):
        config = ConfigParser(allow_unnamed_section=True)
        config.read_string('a=b')
        config.remove_option(UNNAMED_SECTION, 'a')

        for name, key in self.items():
            config.set(UNNAMED_SECTION, name, key)
        config.write(file)

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._data[key] = value

    def __delitem__(self, key):
        del self._data[key]


def load_database(filename):
    with open(filename) as f:
        return Database.load(f)


def save_database(db, filename):
    with open(filename, 'w') as f:
        db.dump(f)


def add_names(names, key, filename):
    if not key:
        raise exceptions.WrongKey(key)
    try:
        b32decode(key.replace(' ', '').upper())
    except:
        raise exceptions.WrongKey(key)
    db = load_database(filename)
    for name in names:
        db[name] = key
    save_database(db, filename)


def del_names(names, filename):
    db = load_database(filename)
    try:
        for name in names:
            del db[name]
    except KeyError as e:
        raise exceptions.NameNotExist(e)
    save_database(db, filename)
