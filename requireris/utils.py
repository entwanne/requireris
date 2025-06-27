import socket


def get_socket_url(sock, *, scheme='http://', resolve=True):
    if sock.family is not socket.AF_INET:
        return f'{scheme}{sock.getsockname()}'

    host, port = sock.getsockname()[:2]
    if resolve and host == '0.0.0.0':
        host = socket.gethostbyname(socket.gethostname())

    return f'{scheme}{host}:{port}'
