import threading
from http.server import HTTPServer

import httpx
import pytest

from requireris.httpd.asgi import ASGIRequestHandler


@pytest.fixture(scope='session')
def server():
    server = HTTPServer(('', 0), ASGIRequestHandler)
    thread = threading.Thread(target=server.serve_forever)
    try:
        thread.start()
        yield server
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture(scope='session')
def url(server):
    return f'http://localhost:{server.server_port}'


@pytest.fixture(scope='session')
def _test_app(server):
    scope_logs = []

    async def app(scope, receive, send):
        scope_logs.append(scope)
        match (scope['method'], scope['path']):
            case ('GET', '/'):
                await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'Content-Type', b'text/plain')]})
                await send({'type': 'http.response.body', 'body': b'Index'})
            case ('GET', '/empty'):
                await send({'type': 'http.response.start', 'status': 204, 'headers': []})
            case ('POST', '/data'):
                data = await receive()
                content_type = next((value for hdr, value in scope['headers'] if hdr == b'content-type'), '')
                await send({'type': 'http.response.start', 'status': 200, 'headers': [(b'Content-Type', content_type)]})
                await send({'type': 'http.response.body', 'body': data['body']})
            case _:
                await send({'type': 'http.response.start', 'status': 404, 'headers': []})
                await send({'type': 'http.response.body', 'body': b'Not found'})

    app.scope_logs = scope_logs
    server.app = app
    return app


@pytest.fixture()
def test_app(_test_app):
    try:
        yield _test_app
    finally:
        _test_app.scope_logs.clear()


@pytest.fixture(scope='session')
def base_headers(server):
    return [
        (b'host', f'localhost:{server.server_port}'.encode()),
        *((name.encode(), value.encode()) for name, value in httpx.Client().headers.items())
    ]


def test_asgi_get(test_app, url, base_headers):
    resp = httpx.get(url)
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/plain'
    assert resp.text == 'Index'
    assert test_app.scope_logs == [{
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'query_string': '',
        'headers': base_headers,
    }]


def test_asgi_get_with_data(test_app, url, base_headers):
    resp = httpx.get(f'{url}?q=search&limit=20', headers={'X-Test': '123'})
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/plain'
    assert resp.text == 'Index'
    assert test_app.scope_logs == [{
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'query_string': 'q=search&limit=20',
        'headers': [*base_headers, (b'x-test', b'123')],
    }]


def test_asgi_get_empty(test_app, url, base_headers):
    resp = httpx.get(f'{url}/empty')
    assert resp.status_code == 204
    assert 'Content-Type' not in resp.headers
    assert resp.text == ''
    assert test_app.scope_logs == [{
        'type': 'http',
        'method': 'GET',
        'path': '/empty',
        'query_string': '',
        'headers': base_headers,
    }]


def test_asgi_post_with_data(test_app, url, base_headers):
    resp = httpx.post(f'{url}/data', json={'key': 'value'})
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'application/json'
    assert resp.text == '{"key":"value"}'
    assert test_app.scope_logs == [{
        'type': 'http',
        'method': 'POST',
        'path': '/data',
        'query_string': '',
        'headers': [*base_headers, (b'content-length', b'15'), (b'content-type', b'application/json')],
    }]


@pytest.mark.parametrize('method', ['GET', 'DELETE', 'CONNECT', 'OPTIONS', 'TRACE'])
def test_asgi_notfound(test_app, url, base_headers, method):
    resp = httpx.request(method, f'{url}/notfound')
    assert resp.status_code == 404
    assert resp.text == 'Not found'
    assert test_app.scope_logs == [{
        'type': 'http',
        'method': method,
        'path': '/notfound',
        'query_string': '',
        'headers': base_headers,
    }]


def test_asgi_notfound_head(test_app, url, base_headers):
    resp = httpx.head(f'{url}/notfound')
    assert resp.status_code == 404
    assert resp.text == ''
    assert test_app.scope_logs == [{
        'type': 'http',
        'method': 'HEAD',
        'path': '/notfound',
        'query_string': '',
        'headers': base_headers,
    }]


@pytest.mark.parametrize('method', ['POST', 'PUT', 'PATCH'])
def test_asgi_notfound_write(test_app, url, base_headers, method):
    resp = httpx.request(method, f'{url}/notfound', content='data')
    assert resp.status_code == 404
    assert resp.text == 'Not found'
    assert test_app.scope_logs == [{
        'type': 'http',
        'method': method,
        'path': '/notfound',
        'query_string': '',
        'headers': [*base_headers, (b'content-length', b'4')],
    }]
