from configparser import ConfigParser, UNNAMED_SECTION
from base64 import b32decode

from . import exceptions


def get_accounts(filename):
    config = ConfigParser(allow_unnamed_section=True)
    config.read(filename)
    if not config.has_section(UNNAMED_SECTION):
        return {}
    values = config[UNNAMED_SECTION]
    return {
        name: key.replace(' ', '').upper()
        for name, key in values.items()
    }


def update_accounts(accounts, filename):
    config = ConfigParser(allow_unnamed_section=True)
    config.read_string('a=b')
    config.remove_option(UNNAMED_SECTION, 'a')
    for name, key in accounts.items():
        config.set(UNNAMED_SECTION, name, key)
    with open(filename, 'w') as f:
        config.write(f)


def add_accounts(names, key, filename):
    if not key:
        raise exceptions.WrongKey(key)
    try:
        b32decode(key.replace(' ', '').upper())
    except:
        raise exceptions.WrongKey(key)
    accounts = get_accounts(filename)
    for name in names:
        accounts[name] = key
    update_accounts(accounts, filename)


def del_accounts(names, filename):
    accounts = get_accounts(filename)
    try:
        for name in names:
            del accounts[name]
    except KeyError as e:
        raise exceptions.NameNotExist(e)
    update_accounts(accounts, filename)
