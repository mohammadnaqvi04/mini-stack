from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import json
from datetime import datetime

@dataclass
class HTTPRequest:
    method: str
    path: str
    headers: Dict[str, str]
    body: Optional[bytes]

    @classmethod
    def parse(cls, data: bytes) -> 'HTTPRequest':
        lines = data.decode('utf-8').split('\r\n')
        request_line = lines[0].split(' ')

        method = request_line[0]
        path = request_line[1]

        headers = {}
        body_index = 0

        for i, line in enumerate(lines[1:], 1):
            if line == '':
                body_index = i + 1
                break
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key] = value

        body = None
        if body_index < len(lines):
            body = '\r\n'.join(lines[body_index:]).encode('utf-8')

        return cls(method=method, path=path, headers=headers, body=body)

@dataclass
class HTTPResponse:
    status_code: int
    status_text: str
    headers: Dict[str, str]
    body: bytes

    def serialize(self) -> bytes:
        response = f"HTTP/1.1 {self.status_code} {self.status_text}\r\n"

        for key, value in self.headers.items():
            response += f"{key}: {value}\r\n"

        response += "\r\n"
        response = response.encode('utf-8')

        if self.body:
            response += self.body

        return response

class SimpleHTTPServer:
    def __init__(self, port: int = 8080):
        self.port = port
        self.routes: Dict[Tuple[str, str], callable] = {}
        self.static_files: Dict[str, bytes] = {}

    def route(self, method: str, path: str):
        def decorator(handler):
            self.routes[(method, path)] = handler
            return handler
        return decorator

    def add_static_file(self, path: str, content: bytes):
        self.static_files[path] = content

    def handle_request(self, request: HTTPRequest) -> HTTPResponse:
        # Check for exact route match
        handler = self.routes.get((request.method, request.path))

        if handler:
            return handler(request)

        # Check for static files
        if request.method == 'GET' and request.path in self.static_files:
            content = self.static_files[request.path]
            return HTTPResponse(
                status_code=200,
                status_text="OK",
                headers={
                    'Content-Type': self._get_content_type(request.path),
                    'Content-Length': str(len(content)),
                    'Date': datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
                },
                body=content
            )

        # 404 Not Found
        return HTTPResponse(
            status_code=404,
            status_text="Not Found",
            headers={'Content-Type': 'text/plain'},
            body=b"404 - Page not found"
        )

    def _get_content_type(self, path: str) -> str:
        if path.endswith('.html'):
            return 'text/html'
        elif path.endswith('.json'):
            return 'application/json'
        elif path.endswith('.txt'):
            return 'text/plain'
        else:
            return 'application/octet-stream'

# Example usage
def create_example_server() -> SimpleHTTPServer:
    server = SimpleHTTPServer()

    @server.route('GET', '/')
    def index(request: HTTPRequest) -> HTTPResponse:
        html = """
        <html>
        <head><title>Network Stack Demo</title></head>
        <body>
            <h1>Simple HTTP Server</h1>
            <p>This server demonstrates application layer protocols.</p>
        </body>
        </html>
        """.encode('utf-8')

        return HTTPResponse(
            status_code=200,
            status_text="OK",
            headers={
                'Content-Type': 'text/html',
                'Content-Length': str(len(html))
            },
            body=html
        )

    @server.route('GET', '/api/status')
    def api_status(request: HTTPRequest) -> HTTPResponse:
        status = {
            'status': 'online',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '1.0.0'
        }

        body = json.dumps(status).encode('utf-8')

        return HTTPResponse(
            status_code=200,
            status_text="OK",
            headers={
                'Content-Type': 'application/json',
                'Content-Length': str(len(body))
            },
            body=body
        )

    return server