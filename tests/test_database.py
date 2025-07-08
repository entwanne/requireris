import textwrap

import pytest

from requireris.database import Database
from requireris.exceptions import MissingSecret, WrongSecret


@pytest.fixture
def database(tmpdir):
    return Database(
        tmpdir / 'requireris.db',
        site1={
            'secret': 'ABCDEFGHIJKLMNOP',
        },
        site2={
            'secret': 'ZYXWVUTSRQPONMLK',
            'key': 'value',
            'key2': 'value2',
        },
    )


@pytest.fixture
def config_file(tmpdir):
    path = tmpdir / 'requireris.db'
    path.write_text(
        textwrap.dedent('''
        [site1]
        secret = 0000000000000000

        [site3]
        secret = 1111111111111111
        comment = test
        ''').lstrip(),
        'utf-8',
    )
    return path


def test_init(database):
    assert database.path is not None
    assert dict(database) == {
        'site1': {
            'secret': 'ABCDEFGHIJKLMNOP',
        },
        'site2': {
            'secret': 'ZYXWVUTSRQPONMLK',
            'key': 'value',
            'key2': 'value2',
        },
    }


def test_init_empty():
    db = Database()
    assert db.path is None
    assert dict(db) == {}


def test_init_missing_secret():
    with pytest.raises(MissingSecret) as e:
        Database(
            foo={},
            bar={'secret': '0'*16},
            baz={'key': 'value'},
        )

    assert e.value.args == (['foo', 'baz'],)


def test_dict_operations(database):
    assert len(database) == 2
    assert database.keys() == {'site1', 'site2'}

    assert database.items() == dict(database).items()
    assert list(database) == ['site1', 'site2']

    assert database['site1'] == {
        'secret': 'ABCDEFGHIJKLMNOP',
    }
    assert database['site2'] == {
        'secret': 'ZYXWVUTSRQPONMLK',
        'key': 'value',
        'key2': 'value2',
    }

    database['site3'] = {
        'secret': 'b' * 16,
        'comment': 'test',
    }
    assert dict(database) == {
        'site1': {
            'secret': 'ABCDEFGHIJKLMNOP',
        },
        'site2': {
            'secret': 'ZYXWVUTSRQPONMLK',
            'key': 'value',
            'key2': 'value2',
        },
        'site3': {
            'secret': 'b' * 16,
            'comment': 'test',
        },
    }

    del database['site2']
    del database['site3']
    assert len(database) == 1
    assert dict(database) == {
        'site1': {
            'secret': 'ABCDEFGHIJKLMNOP',
        },
    }

    del database['site1']
    assert dict(database) == {}


def test_missing_secret(database):
    with pytest.raises(MissingSecret) as e:
        database['site3'] = {
            'comment': 'test',
        }

    assert e.value.args == ('site3',)

    assert database.keys() == {'site1', 'site2'}


def test_wrong_secret(database):
    with pytest.raises(WrongSecret) as e:
        database['site3'] = {
            'secret': '123456',
        }

    assert e.value.args == ('site3',)

    assert database.keys() == {'site1', 'site2'}


def test_load(config_file):
    db = Database(config_file)
    db.load()
    assert dict(db) == {
        'site1': {
            'secret': '0000000000000000',
        },
        'site3': {
            'secret': '1111111111111111',
            'comment': 'test',
        },
    }


def test_load_clear(database, config_file):
    assert database.keys() == {'site1', 'site2'}

    database.load()
    assert dict(database) == {
        'site1': {
            'secret': '0000000000000000',
        },
        'site3': {
            'secret': '1111111111111111',
            'comment': 'test',
        },
    }


def test_load_missing_file(database, mocker):
    mocker.patch.object(database.path, 'open', side_effect=FileNotFoundError)

    with pytest.raises(FileNotFoundError):
        database.load()
    assert dict(database) == {}

    database.load(missing_ok=True)
    assert dict(database) == {}


def test_save(database):
    assert not database.path.exists()

    database.save()
    assert database.path.exists()
    assert database.path.read_text('utf-8') == textwrap.dedent('''
    [site1]
    secret = ABCDEFGHIJKLMNOP

    [site2]
    secret = ZYXWVUTSRQPONMLK
    key = value
    key2 = value2

    ''').lstrip()

    database['site1'] |= {
        'secret': database['site1']['secret'][::-1],
        'foo': 'bar',
        'other': '',
    }

    database.save()
    assert database.path.exists()
    assert database.path.read_text('utf-8') == textwrap.dedent('''
    [site1]
    secret = PONMLKJIHGFEDCBA
    foo = bar
    other = 

    [site2]
    secret = ZYXWVUTSRQPONMLK
    key = value
    key2 = value2

    ''').lstrip()


def test_save_empty(tmpdir):
    path = tmpdir / 'requireris.db'
    assert not path.exists()

    db = Database(path)
    assert dict(db) == {}
    db.save()
    assert path.exists()

    assert path.read_text('utf-8') == ''
