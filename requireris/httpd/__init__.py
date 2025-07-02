from http.server import HTTPServer
from logging import getLogger

from .asgi import ASGIRequestHandler
from ..utils import get_socket_url


logger = getLogger(__name__)


def run_server(db, port, on_started=None):
    from .app import app

    httpd = HTTPServer(('', port), ASGIRequestHandler)
    httpd.app = app

    app.db = db
    app.url = get_socket_url(httpd.socket)

    logger.info('Starting serveur on %s', app.url)
    if on_started:
        on_started(app)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info('Shutting down...')
        httpd.shutdown()
