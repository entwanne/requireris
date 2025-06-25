from fnmatch import fnmatch
from http.server import HTTPServer, BaseHTTPRequestHandler
from importlib import resources
from time import time
import json
import os

from . import exceptions
from .database import load_database, add_names, del_names
from .auth import auth

WWW = resources.files('requireris.www')


def HandlerDB(db_path):
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
        def act_del(self, name):
            try:
                del_names([name], db_path)
            except exceptions.NameNotExist:
                return 'Error: Name «%s» does not exist' % name
            except:
                return 'An error occurred'
            return ''
        def act_add(self, name, key):
            try:
                add_names([name], key, db_path)
            except exceptions.WrongKey as key:
                return 'Error: The key «%s» is not well-formated' % key
            except:
                return 'An error occured'
            return ''
        def act_json_get(self, pattern='*'):
            db = load_database(db_path).items()
            db = ((name, key) for (name, key) in db if fnmatch(name, pattern))
            db = [{"name": name, "auth": auth(key)} for (name, key) in db]
            return json.dumps(db)
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


def opt_http(port, db_path):
    try:
        httpd = HTTPServer(('', port), HandlerDB(db_path))
        print('Starting serveur on http://127.0.0.1:%d' % port)
        httpd.serve_forever()
    except:
        pass
