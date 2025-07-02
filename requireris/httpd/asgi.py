import asyncio
from urllib.parse import urlparse

from http.server import BaseHTTPRequestHandler


class ASGIRequestHandler(BaseHTTPRequestHandler):
    def route(self):
        url = urlparse(self.path)
        scope = {
            'type': 'http',
            'method': self.command,
            'path': url.path,
            'query_string': url.query,
            'headers': [(header.lower().encode(), value.encode()) for header, value in self.headers.items()],
        }

        async def receive():
            content_type = self.headers['Content-Type']
            size = int(self.headers['Content-Length'])
            return {
                'type': 'http.request',
                'body': self.rfile.read(size),
                'more_body': False,
            }

        async def send(data):
            match data['type']:
                case 'http.response.start':
                    self.send_response(data['status'])
                    for header, value in data['headers']:
                        self.send_header(header.decode(), value.decode())
                    self.end_headers()
                case 'http.response.body':
                    self.wfile.write(data['body'])
        asyncio.run(self.server.app(scope, receive, send))

    do_GET = do_POST = do_PUT = do_DELETE = do_HEAD = do_OPTIONS = route
