#!/usr/bin/env python3

import argparse
from fnmatch import fnmatch
from logging import getLogger
from os import getenv
from pathlib import Path
from sys import stderr

from .database import Database
from .exceptions import WrongSecret
from .totp import generate_totp

logger = getLogger(__name__)


def list_keys(db, patterns=(), **kwargs):
    if not db:
        logger.warning('No available key')
        return

    print('Available keys:')
    for key in db.keys():
        if not patterns or any(fnmatch(key, p) for p in patterns):
            print('-', key)


def get_secret(db, keys, **kwargs):
    for key in keys:
        item = dict(db[key])
        secret = item.pop('secret')
        print(f'{key}:')
        print(f'    {generate_totp(secret)}')
        for name, value in item.items():
            print(f'    {name}: {value}')


def add_secret(db, key, secret, **kwargs):
    updated = key in db
    db[key] = (kwargs.get('data') or {}) | {'secret': secret}
    if updated:
        logger.info('Key %s updated', key)
    else:
        logger.info('Key %s inserted', key)
    db.save()


def remove_key(db, keys, **kwargs):
    for key in keys:
        del db[key]
        logger.info('Key %s deleted', key)
    db.save()


def run_http_server(db, port, open=False, **kwargs):
    def open_browser(httpd):
        import webbrowser
        webbrowser.open(httpd.url)

    try:
        from .httpd import run_server
    except ImportError:
        logger.error("HTTP server not available, install requireris[http] dependencies to use it")
    else:
        run_server(db, port, on_started=open_browser if open else None)


class DataDictAction(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        data = {}
        for arg in values:
            key, value = arg.split('=', 1)
            data[key] = value
        setattr(namespace, self.dest, data)


def _get_parser():
    parser = argparse.ArgumentParser(prog='requireris')
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
    append_parser.add_argument('--data', nargs='*', action=DataDictAction)

    delete_parser = subparsers.add_parser('delete', aliases=['del'], help="Delete all secrets for given keys")
    delete_parser.set_defaults(func=remove_key)
    delete_parser.add_argument('keys', nargs='+')

    http_parser = subparsers.add_parser('http', aliases=['server'], help="Run an HTTP server")
    http_parser.set_defaults(func=run_http_server)
    http_parser.add_argument('--port', nargs='?', type=int, default=8080)
    http_parser.add_argument('--open', default=False, action=argparse.BooleanOptionalAction, help="Open website in browser")


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
        logger.error(f"Key {e} was not found in database")
    except WrongSecret:
        logger.error("Given secret is not well-formated")
    except Exception as e:
        logger.error(f"A fatal error occured, please check your database's file: {type(e).__name__}: {e}")


if __name__ == '__main__':
    main()
