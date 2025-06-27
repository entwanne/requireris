from fnmatch import fnmatch
from http.server import HTTPServer, BaseHTTPRequestHandler
from importlib import resources
from time import time
import json
import os

from .exceptions import WrongSecret
from .totp import generate_totp

WWW = resources.files('requireris.www')


def HandlerDB(db):
    class Handler(BaseHTTPRequestHandler):
        def act_static_serve(self, directory):
            def serve(path):
                try:
                    return (WWW / directory / path).read_text()
                except:
                    pass
                return ''
            return serve
        def act_get(self, pattern='*'):
            return (WWW / 'index.html').read_text() % pattern
        def act_del(self, key):
            try:
                del db[key]
            except KeyError:
                return f"Error: Key '{key}' does not exist"
            except Exception:
                return "An error occurred"
            return ''
        def act_add(self, key, secret):
            try:
                db[key] = secret
            except WrongSecret:
                return "Error: Secret is not well-formated"
            except:
                return "An error occured"
            return ''
        def act_json_get(self, pattern='*'):
            entries = ((name, key) for (name, key) in db.items() if fnmatch(name, pattern))
            entries = [{"name": name, "totp": generate_totp(key)} for (name, key) in entries]
            return json.dumps(entries)
        def act_json_timer(self):
            return '{"validity": %d}' % (30 - int(time()) % 30)
        def act_json(self, act, *args):
            actions = {
                'get' : self.act_json_get,
                'timer' : self.act_json_timer
                }
            if act in actions:
                return actions[act](*args)
            return ''
        def do_GET(self):
            actions = {
                '' : self.act_get,
                'get' : self.act_get,
                'add' : self.act_add,
                'del' : self.act_del,
                'js' : self.act_static_serve('js'),
                'css' : self.act_static_serve('css'),
                'img' : self.act_static_serve('img'),
                'json' : self.act_json
                }
            act, *args = self.path[1:].split('/')
            if act in actions:
                content = actions[act](*args)
            else:
                content = ''
            if not isinstance(content, bytes):
                self.send_response(200)
                self.send_header('Content-type','text/html')
                self.end_headers()
                content = content.encode()
            self.wfile.write(content)
    return Handler


def run_server(db, port):
    try:
        httpd = HTTPServer(('', port), HandlerDB(db))
        print('Starting serveur on http://127.0.0.1:%d' % port)
        httpd.serve_forever()
    except Exception:
        pass
