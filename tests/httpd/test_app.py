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


def test_index_json(cli):
    resp = cli.get('/')
    assert resp.status_code == 200
    assert resp.json() == {
        'keys': {
            'site1': {
                '@get': {
                    'method': 'GET',
                    'href': f'{URL}/get/site1',
                },
            },
            'site2': {
                '@get': {
                    'method': 'GET',
                    'href': f'{URL}/get/site2',
                },
            },
        },
        '@list': {
            'method': 'GET',
            'href': URL,
        },
        '@insert': {
            '@method': 'POST',
            'href': f'{URL}/new',
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
    assert 'site1' in resp.text
    assert 'site2' in resp.text
    assert 'TOTP' not in resp.text


@pytest.mark.parametrize('key,code,extra', [
    ('site1', '235656', {}),
    ('site2', '369886', {'foo': 'bar'}),
])
def test_get_key_json(cli, key, code, extra):
    resp = cli.get(f'/get/{key}')
    assert resp.status_code == 200
    assert resp.json() == {
        'code': code,
        **extra,
        '@list': {
            'method': 'GET',
            'href': URL,
        },
        '@get': {
            'method': 'GET',
            'href': f'{URL}/get/{key}',
        },
        '@update': {
            'method': 'PUT',
            'href': f'{URL}/update/{key}',
            'template': {
                'secret': 'string',
            },
        },
        '@delete': {
            'method': 'DELETE',
            'href': f'{URL}/del/{key}',
        },
    }


def test_get_key_json_not_found(cli):
    resp = cli.get(f'/get/site3')
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


def test_insert_key_json(cli, database):
    assert 'site3' not in database

    resp = cli.post('/new', json={'key': 'site3', 'secret': 'EFEFEFEF'})
    assert resp.status_code == 200

    assert database['site3'] == {
        'secret': 'EFEFEFEF',
    }

    assert resp.json() == cli.get('/get/site3').json()

    # Check database was saved

    db2 = Database(database.path)
    db2.load()
    assert db2['site3'] == database['site3']


def test_insert_key_json_extra_data(cli, database):
    resp = cli.post('/new', json={'key': 'site3', 'secret': 'EFEFEFEF', 'extra_key': 'extra_value'})
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

    resp = cli.post('/new', json={'key': 'site2', 'secret': 'EFEFEFEF', 'extra_key': 'extra_value'})
    assert resp.status_code == 200
    assert database['site2'] == {
        'secret': 'EFEFEFEF',
        'extra_key': 'extra_value',
    }


def test_insert_key_json_missing_data(cli, database):
    resp = cli.post('/new', json={})
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


@pytest.mark.parametrize('method', ['DELETE', 'POST'])
def test_delete_key_json(cli, database, method):
    assert 'site2' in database

    resp = cli.request(method, '/del/site2')
    assert resp.status_code == 204

    assert 'site2' not in database

    # Check database was saved

    db2 = Database(database.path)
    db2.load()
    assert 'site1' in db2
    assert 'site2' not in db2


def test_delete_key_json_not_found(cli, database):
    resp = cli.delete('/del/site3')
    assert resp.status_code == 404


def test_delete_key_html(html_cli, database):
    assert 'site2' in database

    resp = html_cli.post('/del/site2')
    assert resp.status_code == 200
    assert resp.text == html_cli.get('/').text

    assert 'site2' not in database


@pytest.mark.parametrize('method', ['PUT', 'POST', 'PATCH'])
def test_update_key_json(cli, database, method):
    resp = cli.request(method, '/update/site2', json={'secret': 'EFEFEFEF', 'extra_key': 'extra_value'})
    assert resp.status_code == 200
    assert resp.json() == cli.get('/get/site2').json()

    assert database['site2'] == {
        'secret': 'EFEFEFEF',
        'extra_key': 'extra_value',
    }

    # Check database was saved

    db2 = Database(database.path)
    db2.load()
    assert db2['site2'] == database['site2']


def test_update_key_json_empty_data(cli, database):
    resp = cli.put('/update/site2', json={})
    assert resp.status_code == 200
    assert resp.json() == cli.get('/get/site2').json()

    assert database['site2'] == {
        'secret': 'CDCDCDCD',
    }


def test_update_key_json_not_found(cli, database):
    resp = cli.put('/update/site3', json={'secret': 'EFEFEFEF'})
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
