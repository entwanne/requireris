import socket
import socketserver

import pytest

from requireris.utils import get_socket_url


@pytest.mark.parametrize('server_cls', [socketserver.TCPServer, socketserver.UDPServer])
def test_get_socket_url_inet_localhost(server_cls):
    server = server_cls(('localhost', 0), socketserver.BaseRequestHandler)
    _, port = server.socket.getsockname()

    assert get_socket_url(server.socket) == f'http://127.0.0.1:{port}'
    assert get_socket_url(server.socket, scheme='ftp://') == f'ftp://127.0.0.1:{port}'
    assert get_socket_url(server.socket, resolve=False) == f'http://127.0.0.1:{port}'


@pytest.mark.parametrize('server_cls', [socketserver.TCPServer, socketserver.UDPServer])
def test_get_socket_url_inet_network(server_cls):
    server = server_cls(('0.0.0.0', 0), socketserver.BaseRequestHandler)
    _, port = server.socket.getsockname()
    network_host = socket.gethostbyname(socket.gethostname())

    assert get_socket_url(server.socket) == f'http://{network_host}:{port}'
    assert get_socket_url(server.socket, scheme='ftp://') == f'ftp://{network_host}:{port}'
    assert get_socket_url(server.socket, resolve=False) == f'http://0.0.0.0:{port}'


def test_get_socket_url_unix(tmp_path):
    addr = str(tmp_path / 'server.socket')
    server = socketserver.UnixStreamServer(addr, socketserver.BaseRequestHandler)

    assert get_socket_url(server.socket, scheme='file://') == f'file://{addr}'
