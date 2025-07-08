import pytest
from fastapi.testclient import TestClient

from requireris.database import Database


URL = 'http://test.localhost'


@pytest.fixture()
def database(tmpdir):
    return Database(
        tmpdir / 'requireris.db',
        site1={'secret': 'ABABABAB'},
        site2={'secret': 'CDCDCDCD', 'foo': 'bar'},
    )


@pytest.fixture()
def app(database):
    from requireris.httpd.app import app
    app.db = database
    app.url = URL
    return app


@pytest.fixture()
def cli(app):
    return TestClient(app)


@pytest.fixture(params=['text/html', 'application/xhtml+xml'])
def html_cli(app, request):
    return TestClient(app, headers={'Accept': request.param})


@pytest.fixture(autouse=True)
def freeze_time(mocker):
    mocker.patch('time.time', return_value=123456)


@pytest.mark.parametrize('path', ['/', '/keys'])
def test_index_json(cli, path):
    resp = cli.get(path)
    assert resp.status_code == 200
    assert resp.json() == {
        'keys': {
            'site1': {
                '@get': {
                    'method': 'GET',
                    'href': f'{URL}/keys/site1',
                },
            },
            'site2': {
                '@get': {
                    'method': 'GET',
                    'href': f'{URL}/keys/site2',
                },
            },
        },
        '@list': {
            'method': 'GET',
            'href': f'{URL}/keys',
        },
        '@insert': {
            '@method': 'POST',
            'href': f'{URL}/keys',
            'template': {
                'key': 'string',
                'secret': 'string',
            },
        },
    }


def test_index_html(html_cli):
    resp = html_cli.get('/')
    assert resp.status_code == 200
    assert resp.text.startswith('<!DOCTYPE html>')
    assert 'get/site1' in resp.text
    assert 'get/site2' in resp.text
    assert 'TOTP' not in resp.text


@pytest.mark.parametrize('key,path,code,extra', [
    ('site1', '/keys/site1', '235656', {}),
    ('site2', '/get/site2', '369886', {'foo': 'bar'}),
])
def test_get_key_json(cli, key, path, code, extra):
    resp = cli.get(path)
    assert resp.status_code == 200
    assert resp.json() == {
        'code': code,
        **extra,
        '@list': {
            'method': 'GET',
            'href': f'{URL}/keys',
        },
        '@get': {
            'method': 'GET',
            'href': f'{URL}/keys/{key}',
        },
        '@update': {
            'method': 'PUT',
            'href': f'{URL}/keys/{key}',
            'template': {
                'secret': 'string',
            },
        },
        '@delete': {
            'method': 'DELETE',
            'href': f'{URL}/keys/{key}',
        },
    }


def test_get_key_json_not_found(cli):
    resp = cli.get(f'/keys/site3')
    assert resp.status_code == 404
    assert resp.json() == {'detail': "Key 'site3' not found"}


def test_get_key_html(html_cli):
    resp = html_cli.get('/get/site1')
    assert resp.status_code == 200
    assert resp.text.startswith('<!DOCTYPE html>')
    assert 'site1' in resp.text
    assert 'TOTP code: <b>235656</b>' in resp.text
    assert 'site2' not in resp.text


def test_get_key_html_not_found(html_cli):
    resp = html_cli.get('/get/site3')
    assert resp.status_code == 404


@pytest.mark.parametrize('path', ['/keys', '/new'])
def test_insert_key_json(cli, database, path):
    assert 'site3' not in database

    resp = cli.post(path, json={'key': 'site3', 'secret': 'EFEFEFEF'})
    assert resp.status_code == 200

    assert database['site3'] == {
        'secret': 'EFEFEFEF',
    }

    assert resp.json() == cli.get('/keys/site3').json()

    # Check database was saved

    db2 = Database(database.path)
    db2.load()
    assert db2['site3'] == database['site3']


def test_insert_key_json_extra_data(cli, database):
    resp = cli.post('/keys', json={'key': 'site3', 'secret': 'EFEFEFEF', 'extra_key': 'extra_value'})
    assert resp.status_code == 200

    assert database['site3'] == {
        'secret': 'EFEFEFEF',
        'extra_key': 'extra_value',
    }


def test_insert_key_json_existing_key(cli, database):
    assert database['site2'] == {
        'secret': 'CDCDCDCD',
        'foo': 'bar',
    }

    resp = cli.post('/keys', json={'key': 'site2', 'secret': 'EFEFEFEF', 'extra_key': 'extra_value'})
    assert resp.status_code == 200
    assert database['site2'] == {
        'secret': 'EFEFEFEF',
        'extra_key': 'extra_value',
    }


def test_insert_key_json_missing_data(cli, database):
    resp = cli.post('/keys', json={})
    assert resp.status_code == 422
    assert 'site3' not in database

    errors = [
        (record['type'], record['msg'], record['loc'])
        for record in resp.json()['detail']
    ]
    assert errors == [
        ('missing', 'Field required', ['key']),
        ('missing', 'Field required', ['secret']),
    ]


def test_insert_key_html(html_cli, database):
    assert 'site3' not in database

    resp = html_cli.post('/new', data={'key': 'site3', 'secret': 'EFEFEFEF'})
    assert resp.status_code == 200

    assert database['site3'] == {
        'secret': 'EFEFEFEF',
    }

    assert resp.text == html_cli.get('/get/site3').text 


def test_insert_key_html_missing_data(html_cli, database):
    resp = html_cli.post('/new', data={})
    assert resp.status_code == 422
    assert 'site3' not in database

    errors = [
        (record['type'], record['msg'], record['loc'])
        for record in resp.json()['detail']
    ]
    assert errors == [
        ('missing', 'Field required', ['key']),
        ('missing', 'Field required', ['secret']),
    ]


@pytest.mark.parametrize('method,path', [
    ('DELETE', '/keys/site2'),
    ('POST', '/del/site2'),
])
def test_delete_key_json(cli, database, method, path):
    assert 'site2' in database

    resp = cli.request(method, path)
    assert resp.status_code == 204

    assert 'site2' not in database

    # Check database was saved

    db2 = Database(database.path)
    db2.load()
    assert 'site1' in db2
    assert 'site2' not in db2


def test_delete_key_json_not_found(cli, database):
    resp = cli.delete('/keys/site3')
    assert resp.status_code == 404


def test_delete_key_html(html_cli, database):
    assert 'site2' in database

    resp = html_cli.post('/del/site2')
    assert resp.status_code == 200
    assert resp.text == html_cli.get('/').text

    assert 'site2' not in database


@pytest.mark.parametrize('method,path,old_values', [
    ('PUT', '/keys/site2', {}),
    ('PATCH', '/keys/site2', {'foo': 'bar'}),
    ('POST', '/update/site2', {}),
])
def test_update_key_json(cli, database, method, path, old_values):
    resp = cli.request(method, path, json={'secret': 'EFEFEFEF', 'extra_key': 'extra_value'})
    assert resp.status_code == 200
    assert resp.json() == cli.get('/keys/site2').json()

    assert database['site2'] == {
        'secret': 'EFEFEFEF',
        'extra_key': 'extra_value',
        **old_values,
    }

    # Check database was saved

    db2 = Database(database.path)
    db2.load()
    assert db2['site2'] == database['site2']


def test_update_key_json_empty_data(cli, database):
    resp = cli.put('/keys/site2', json={})
    assert resp.status_code == 200
    assert resp.json() == cli.get('/keys/site2').json()

    assert database['site2'] == {
        'secret': 'CDCDCDCD',
    }


def test_update_key_json_not_found(cli, database):
    resp = cli.put('/keys/site3', json={'secret': 'EFEFEFEF'})
    assert resp.status_code == 200
    assert resp.json() == cli.get('/get/site3').json()

    assert database['site3'] == {
        'secret': 'EFEFEFEF',
    }


def test_update_key_html(html_cli, database):
    resp = html_cli.post('/update/site2', data={'secret': 'EFEFEFEF', 'extra_key': 'extra_value'})
    assert resp.status_code == 200

    assert database['site2'] == {
        'secret': 'EFEFEFEF',
        'extra_key': 'extra_value',
    }

    assert resp.text == html_cli.get('/get/site2').text
