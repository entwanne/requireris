#!/usr/bin/env python3

from argparse import ArgumentParser
from os import getenv
from pathlib import Path
from sys import stderr

from . import exceptions
from .database import Database
from .opts import opt_list, opt_get, opt_append, opt_delete
from .httpd import opt_http


def print_err(*args, **kwargs):
    kwargs['file'] = stderr
    return print(*args, **kwargs)


def _get_parser():
    parser = ArgumentParser(prog='requireris')
    parser.set_defaults(func=lambda args, db: opt_list(db, *args.patterns))
    parser.set_defaults(patterns=[])

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

    list_parser = subparsers.add_parser('list')
    list_parser.add_argument('patterns', nargs='*')

    get_parser = subparsers.add_parser('get')
    get_parser.set_defaults(func=lambda args, db: opt_get(db, *args.names))
    get_parser.add_argument('names', nargs='+')

    append_parser = subparsers.add_parser('append', aliases=['add'], help="Append/Update key for name mentioned")
    append_parser.set_defaults(func=lambda args, db: opt_append(db, args.name, args.key))
    append_parser.add_argument('name')
    append_parser.add_argument('key')

    delete_parser = subparsers.add_parser('delete', aliases=['del'], help="Delete all entries for names mentioned")
    delete_parser.set_defaults(func=lambda args, db: opt_delete(db, *args.names))
    delete_parser.add_argument('names', nargs='+')

    http_parser = subparsers.add_parser('http', aliases=['server'], help="Run an HTTP server")
    http_parser.set_defaults(func=lambda args, db: opt_http(db, args.port))
    http_parser.add_argument('--port', nargs='?', type=int, default=8080)

    return parser


parser = _get_parser()


def main():
    args = parser.parse_args()
    if args.db_path is None:
        args.db_path = args.db_dir / args.db_file

    db = Database(args.db_path)
    db.load(missing_ok=True)

    args.func(args, db)


if __name__ == '__main__':
    try:
        main()
    except exceptions.NameNotExist as name:
        print_err('Name %s does not exist' % name)
    except exceptions.WrongKey as key:
        print_err("The key '%s' is not well-formated" % key)
    except exceptions.NoNamesSelected:
        print_err('You should select names to execute this operation')
    except:
        print_err("A fatal error occured, please check your database's file")
