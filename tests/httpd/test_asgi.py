import threading
from http.server import HTTPServer

import httpx
import pytest

from requireris.httpd.asgi import ASGIRequestHandler


@pytest.fixture()
def server():
    server = HTTPServer(('', 0), ASGIRequestHandler)
    thread = threading.Thread(target=server.serve_forever)
    try:
        thread.start()
        yield server
    finally:
        server.shutdown()
        thread.join()


@pytest.fixture()
def url(server):
    return f'http://localhost:{server.server_port}'


def test_asgi_request_handler(server, url):
    scope_logs = []

    async def application(scope, receive, send):
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

    server.app = application

    base_headers = [
        (b'host', f'localhost:{server.server_port}'.encode()),
        *((name.encode(), value.encode()) for name, value in httpx.Client().headers.items())
    ]

    resp = httpx.get(url)
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/plain'
    assert resp.text == 'Index'
    assert scope_logs.pop() == {
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'query_string': '',
        'headers': base_headers,
    }

    resp = httpx.get(f'{url}?q=search&limit=20', headers={'X-Test': '123'})
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'text/plain'
    assert resp.text == 'Index'
    assert scope_logs.pop() == {
        'type': 'http',
        'method': 'GET',
        'path': '/',
        'query_string': 'q=search&limit=20',
        'headers': [*base_headers, (b'x-test', b'123')],
    }

    resp = httpx.get(f'{url}/empty')
    assert resp.status_code == 204
    assert 'Content-Type' not in resp.headers
    assert resp.text == ''
    assert scope_logs.pop() == {
        'type': 'http',
        'method': 'GET',
        'path': '/empty',
        'query_string': '',
        'headers': base_headers,
    }

    resp = httpx.post(f'{url}/data', json={'key': 'value'})
    assert resp.status_code == 200
    assert resp.headers['Content-Type'] == 'application/json'
    assert resp.text == '{"key":"value"}'
    assert scope_logs.pop() == {
        'type': 'http',
        'method': 'POST',
        'path': '/data',
        'query_string': '',
        'headers': [*base_headers, (b'content-length', b'15'), (b'content-type', b'application/json')],
    }

    resp = httpx.get(f'{url}/notfound')
    assert resp.status_code == 404
    assert resp.text == 'Not found'
    assert scope_logs.pop() == {
        'type': 'http',
        'method': 'GET',
        'path': '/notfound',
        'query_string': '',
        'headers': base_headers,
    }
