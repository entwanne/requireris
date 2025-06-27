import json
import os
from fnmatch import fnmatch
from http.server import HTTPServer, BaseHTTPRequestHandler
from importlib import resources
from time import time
from urllib.parse import parse_qsl

from jinja2 import Environment, PackageLoader, select_autoescape

from .totp import generate_totp


class RequestHandler(BaseHTTPRequestHandler):
    @property
    def env(self):
        return self.server.env

    @property
    def db(self):
        return self.server.db

    def render_template(self, tpl_path, **kwargs):
        template = self.env.get_template(tpl_path)
        content = template.render(**kwargs)

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode())

    def redirect(self, location):
        self.send_response(303)
        self.send_header('Location', location)
        self.end_headers()

    def get_data(self):
        size = int(self.headers['Content-Length'])
        raw = self.rfile.read(size)
        return {
            key: value
            for key, value in parse_qsl(raw.decode())
        }

    def index(self):
        return self.render_template('index.html', keys=self.db.keys())

    def get_key(self, key):
        return self.render_template(
            'get.html',
            key=key,
            code=generate_totp(self.db[key]),
        )

    def insert_key(self):
        data = self.get_data()
        key = data['key']
        self.db[key] = data['secret']
        self.db.save()
        self.redirect(f'/get/{key}')

    def update_key(self, key):
        data = self.get_data()
        self.db[key] = data['secret']
        self.db.save()
        self.redirect(f'/get/{key}')

    def delete_key(self, key):
        del self.db[key]
        self.db.save()
        self.redirect('/')

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
    print('Starting serveur on http://127.0.0.1:%d' % port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
