#!/usr/bin/env python3

from argparse import ArgumentParser
from sys import stderr

from . import exceptions
from .opts import opt_get, opt_append, opt_delete
from .httpd import opt_http


def print_err(*args, **kwargs):
    kwargs['file'] = stderr
    return print(*args, **kwargs)


def _get_parser():
    parser = ArgumentParser(prog='requireris')
    parser.set_defaults(func='GET')

    subparsers = parser.add_subparsers(required=False)

    get_parser = subparsers.add_parser('get')

    append_parser = subparsers.add_parser('append', aliases=['add'], help="Append/Update key for users mentioned")
    append_parser.set_defaults(func='ADD')
    append_parser.add_argument('key')

    delete_parser = subparsers.add_parser('delete', aliases=['del'], help="Delete all entries for users mentioned")
    delete_parser.set_defaults(func='DEL')

    http_parser = subparsers.add_parser('http', aliases=['server'], help="Run an HTTP server")
    http_parser.set_defaults(func='HTTP')
    http_parser.add_argument('--port', nargs='?', type=int, default=8080)

    for p in (parser, get_parser, append_parser, delete_parser, http_parser):
        p.add_argument('-u', '--user', nargs='*', dest='users')
        p.add_argument('--db', '--file', nargs='?', default='.requireris', help="Database's filename")

    return parser


parser = _get_parser()


def main():
    args = parser.parse_args()
    match args.func:
        case 'HTTP':
            return opt_http(args.port, args.db)
        case 'DEL':
            return opt_delete(args.users, args.db)
        case 'ADD':
            return opt_append(args.users, args.key, args.db)
        case _:
            return opt_get(args.users, args.db)


if __name__ == '__main__':
    try:
        main()
    except exceptions.UserNotExist as user:
        print_err('User %s does not exist' % user)
    except exceptions.WrongKey as key:
        print_err("The key '%s' is not well-formated" % key)
    except exceptions.NoUsersSelected:
        print_err('You should select users to execute this operation')
    except:
        print_err("A fatal error occured, please check your database's file")
