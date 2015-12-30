import csv
from base64 import b32decode

import exceptions

def get_accounts(filename):
    with open(filename) as csvfile:
        reader = csv.reader(csvfile, delimiter=':')
        return {user:key.replace(' ', '').upper() for (user, key) in reader}
    return None

def update_accounts(accounts, filename):
    with open(filename, 'w') as csvfile:
        writer = csv.writer(csvfile, delimiter=':')
        for user, key in accounts.items():
            writer.writerow([user, key])

def add_accounts(users, key, filename):
    if not key:
        raise exceptions.WrongKey(key)
    try:
        b32decode(key.replace(' ', '').upper())
    except:
        raise exceptions.WrongKey(key)
    accounts = get_accounts(filename)
    for user in users:
        accounts[user] = key
    update_accounts(accounts, filename)

def del_accounts(users, filename):
    accounts = get_accounts(filename)
    try:
        for user in users:
            del accounts[user]
    except KeyError as e:
        raise exceptions.UserNotExist(e)
    update_accounts(accounts, filename)
    
