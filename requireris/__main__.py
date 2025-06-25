#!/usr/bin/env python3

from sys import stderr

import clize

from . import exceptions
from .opts import opt_get, opt_append, opt_delete
from .httpd import opt_http


def print_err(*args, **kwargs):
    kwargs['file'] = stderr
    return print(*args, **kwargs)


@clize.clize(
    alias = {
        'delete' : ('del', 'd'),
        'append' : ('add', 'a', 'update', 'u'),
        'key' : ('k',),
        'db' : ('file', 'f'),
        'http' : ('server', 's'),
        'port' : ('p',)
        }
)
def main(delete=False, append=False, key='', db='.requireris', http=False, port=8080, *users):
    """
    Requireris - Google Authentication's implementation

    users: List of users

    delete: Delete all entries for users mentioned

    append: Append/Update key for users mentioned

    key: Key for append operation

    db: Database's filename

    http: Run an HTTP server

    port: Port for this HTTP server
    """
    if http:
        return opt_http(port, db)
    if delete:
        return opt_delete(users, db)
    if append:
        return opt_append(users, key, db)
    return opt_get(users, db)


if __name__ == '__main__':
    try:
        clize.run(main)
    except exceptions.UserNotExist as user:
        print_err('User %s does not exist' % user)
    except exceptions.WrongKey as key:
        print_err("The key '%s' is not well-formated" % key)
    except exceptions.NoUsersSelected:
        print_err('You should select users to execute this operation')
    except:
        print_err("A fatal error occured, please check your database's file")
