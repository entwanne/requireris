import json
import os
from fnmatch import fnmatch
from http.server import HTTPServer, BaseHTTPRequestHandler
from importlib import resources
from logging import getLogger
from time import time
from urllib.parse import parse_qsl

from jinja2 import Environment, PackageLoader, select_autoescape

from .totp import generate_totp
from .utils import get_socket_url

logger = getLogger(__name__)


class RequestHandler(BaseHTTPRequestHandler):
    @property
    def env(self):
        return self.server.env

    @property
    def db(self):
        return self.server.db

    @property
    def server_url(self):
        return self.server.url

    def render_template(self, tpl_path, **kwargs):
        template = self.env.get_template(tpl_path)
        content = template.render(**kwargs)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())

    def json_response(self, payload):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(payload, indent=2).encode())

    def redirect(self, location):
        self.send_response(303)
        self.send_header('Location', location)
        self.end_headers()

    def get_data(self):
        content_type = self.headers['Content-Type']
        size = int(self.headers['Content-Length'])
        raw_data = self.rfile.read(size).decode()
        if content_type == 'application/json':
            return json.loads(raw_data)
        else:
            return {
                key: value
                for key, value in parse_qsl(raw_data)
            }

    def accept_html(self):
        accept = self.headers['Accept']
        return 'text/html' in accept or 'application/xhtml+xml' in accept

    def index(self):
        if self.accept_html():
            return self.render_template('index.html', keys=self.db.keys())
        return self.json_response({
            'keys': {
                key: {
                    '@get': {
                        'method': 'GET',
                        'href': f'{self.server_url}/get/{key}',
                    },
                }
                for key in self.db.keys()
            },
            '@list': {
                'method': 'GET',
                'href': self.server_url,
            },
            '@insert': {
                '@method': 'POST',
                'href': f'{self.server_url}/new',
                'template': {
                    'key': 'string',
                    'secret': 'string',
                },
            },
        })

    def get_key(self, key):
        code = generate_totp(self.db[key])
        if self.accept_html():
            return self.render_template(
                'get.html',
                key=key,
                code=code,
            )
        return self.json_response({
            'code': code,
            '@list': {
                'method': 'GET',
                'href': self.server_url,
            },
            '@update': {
                'method': 'POST',
                'href': f'{self.server_url}/update/{key}',
                'template': {
                    'secret': 'string',
                },
            },
            '@delete': {
                'method': 'POST',
                'href': f'{self.server_url}/del/{key}',
            },
        })

    def insert_key(self):
        data = self.get_data()
        key = data['key']
        self.db[key] = data['secret']
        self.db.save()
        if self.accept_html():
            self.redirect(f'/get/{key}')
        else:
            self.get_key(key)

    def update_key(self, key):
        data = self.get_data()
        self.db[key] = data['secret']
        self.db.save()
        if self.accept_html():
            self.redirect(f'/get/{key}')
        else:
            self.get_key(key)

    def delete_key(self, key):
        del self.db[key]
        self.db.save()
        if self.accept_html():
            self.redirect('/')
        else:
            self.index()

    routes = {
        ('GET', ''): index,
        ('GET', 'get'): get_key,
        ('POST', 'new'): insert_key,
        ('POST', 'update'): update_key,
        ('POST', 'del'): delete_key,
    }

    def route(self):
        target, *args = self.path[1:].split('/')
        route_func = self.routes.get((self.command, target))
        if route_func is not None:
            route_func(self, *args)
        else:
            self.send_error(404)

    do_GET = do_POST = route


def run_server(db, port):
    env = Environment(
        loader=PackageLoader('requireris.www'),
        autoescape=select_autoescape()
    )
    httpd = HTTPServer(('', port), RequestHandler)
    httpd.env = env
    httpd.db = db
    httpd.url = get_socket_url(httpd.socket)
    logger.info('Starting serveur on %s', httpd.url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logger.info('Shutting down...')
        httpd.shutdown()
