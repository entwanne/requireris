from http.server import HTTPServer, BaseHTTPRequestHandler
from time import time
import json
import os

from . import exceptions
from .account import get_accounts, add_accounts, del_accounts
from .auth import auth
from .match import match


def HandlerDB(db):
    class Handler(BaseHTTPRequestHandler):
        def act_static_serve(self, directory):
            def serve(path):
                try:
                    with open(os.path.join(directory, path), 'rb') as f:
                        return f.read()
                except:
                    pass
                return ''
            return serve
        def act_get(self, pattern='*'):
            with open('www/index.html') as f:
                return f.read() % pattern
            return ''
        def act_del(self, user):
            try:
                del_accounts([user], db)
            except exceptions.UserNotExist as user:
                return 'Error: User «%s» does not exist' % user
            except:
                return 'An error occurred'
            return ''
        def act_add(self, user, key):
            try:
                add_accounts([user], key, db)
            except exceptions.WrongKey as key:
                return 'Error: The key «%s» is not well-formated' % key
            except:
                return 'An error occured'
            return ''
        def act_json_get(self, pattern='*'):
            accounts = get_accounts(db).items()
            accounts = ((user, key) for (user, key) in accounts if match(user, pattern))
            accounts = [{"user": user, "auth": auth(key)} for (user, key) in accounts]
            return json.dumps(accounts)
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
                'js' : self.act_static_serve('www/js'),
                'css' : self.act_static_serve('www/css'),
                'img' : self.act_static_serve('www/img'),
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


def opt_http(port, db):
    try:
        httpd = HTTPServer(('', port), HandlerDB(db))
        print('Starting serveur on http://127.0.0.1:%d' % port)
        httpd.serve_forever()
    except:
        pass
