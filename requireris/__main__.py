#!/usr/bin/env python3

from argparse import ArgumentParser
from fnmatch import fnmatch
from os import getenv
from pathlib import Path
from sys import stderr

from .database import Database
from .exceptions import WrongSecret
from .httpd import run_server
from .totp import generate_totp


def print_err(*args, **kwargs):
    return print(*args, file=stderr, **kwargs)


def list_keys(db, patterns=(), **kwargs):
    if not db:
        print('No available key')
        return

    print('Available keys:')
    for key in db.keys():
        if not patterns or any(fnmatch(key, p) for p in patterns):
            print('-', key)


def get_secret(db, keys, **kwargs):
    for key in keys:
        print(f'{key}: {generate_totp(db[key])}')


def add_secret(db, key, secret, **kwargs):
    word = 'updated' if key in db else 'inserted'
    db[key] = secret
    print('Key', key, word)
    db.save()


def remove_key(db, keys, **kwargs):
    for key in keys:
        del db[key]
        print('Key', key, 'deleted')
    db.save()


def run_http_server(db, port, **kwargs):
    run_server(db, port)


def _get_parser():
    parser = ArgumentParser(prog='requireris')
    parser.set_defaults(func=list_keys, patterns=[])

    parser.add_argument(
        '--db-path',
        nargs='?',
        type=Path,
        default=getenv('REQUIRERIS_DB_PATH'),
        help="Path to current database file (defaulting to REQUIRERIS_DB_PATH env variable or computed with db-dir and db-file)",
    )
    parser.add_argument(
        '--db-dir',
        nargs='?',
        type=Path,
        default=Path(getenv('REQUIRERIS_DB_DIR', Path.home() / '.config')),
        help="Directory of current database file"
    )
    parser.add_argument(
        '--db-file',
        nargs='?',
        default=getenv('REQUIRERIS_DB_FILE', 'requireris.db'),
        help="Name of current database file",
    )

    subparsers = parser.add_subparsers(required=False)

    list_parser = subparsers.add_parser('list', help="List all keys or all keys that match given patterns")
    list_parser.add_argument('patterns', nargs='*')

    get_parser = subparsers.add_parser('get', help="Get all secrets for given keys")
    get_parser.set_defaults(func=get_secret)
    get_parser.add_argument('keys', nargs='+')

    append_parser = subparsers.add_parser('append', aliases=['add'], help="Append or update secret for given key")
    append_parser.set_defaults(func=add_secret)
    append_parser.add_argument('key')
    append_parser.add_argument('secret')

    delete_parser = subparsers.add_parser('delete', aliases=['del'], help="Delete all secrets for given keys")
    delete_parser.set_defaults(func=remove_key)
    delete_parser.add_argument('keys', nargs='+')

    http_parser = subparsers.add_parser('http', aliases=['server'], help="Run an HTTP server")
    http_parser.set_defaults(func=run_http_server)
    http_parser.add_argument('--port', nargs='?', type=int, default=8080)

    return parser


parser = _get_parser()


def main():
    try:
        args = parser.parse_args()
        if args.db_path is None:
            args.db_path = args.db_dir / args.db_file

        db = Database(args.db_path)
        db.load(missing_ok=True)

        args.func(db, **vars(args))
    except KeyError as e:
        print_err(f"Key {e} was not found in database")
    except WrongSecret:
        print_err("Given secret is not well-formated")
    except Exception as e:
        print_err(f"A fatal error occured, please check your database's file: {e}")


if __name__ == '__main__':
    main()
