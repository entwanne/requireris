import csv
from base64 import b32decode

from . import exceptions


def get_accounts(filename):
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=':')
        return {name:key.replace(' ', '').upper() for (name, key) in reader}
    return None


def update_accounts(accounts, filename):
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=':')
        for name, key in accounts.items():
            writer.writerow([name, key])


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
