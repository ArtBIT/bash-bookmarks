#!/usr/bin/env python3
"""
    Create simple HTTP server to handle requests from client, get the
    search value, use it to fuzzy search the files in the directory and
    send back the results to the client
"""

import os
import json
import logging
import ssl
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# Upstream bookmarks server that actually stores the bookmarks
BOOKMARKS_SERVER_URL = os.environ.get('BOOKMARKS_SERVER_URL', 'http://localhost:9080').rstrip('/')

# Optional TLS, required for installing the web UI as a PWA from a non-localhost origin
TLS_CERT = os.environ.get('BOOKMARKS_TLS_CERT', '')
TLS_KEY = os.environ.get('BOOKMARKS_TLS_KEY', '')

STATIC_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')

# Paths that serve the web UI (/share is the PWA share target)
APP_PATHS = ['/', '/share', '/index.html']

# set env debug level
level = os.environ.get('DEBUG', 'INFO')
logging.basicConfig(filename='bookmarks-server.log', level=level)

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Bookmarks</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css" />
    <link rel="icon" type="image/png" href="/favicon.png">
  </head>
  <body>
    <main class="container">
    {}
    </main>
  </body>
</html>
""";


class Server:
    def __init__(self, port):
        self.port = port

    def run(self):
        """
            Run the server
        """
        logging.info('Server running on port {}'.format(self.port))
        server_address = ('0.0.0.0', self.port)
        httpd = ThreadingHTTPServer(server_address, ServerHandler)
        if TLS_CERT and TLS_KEY:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(TLS_CERT, TLS_KEY)
            httpd.socket = context.wrap_socket(httpd.socket, server_side=True)
            logging.info('TLS enabled')
        httpd.serve_forever()

class ServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
            Handle GET request from client
        """
        path = urllib.parse.urlsplit(self.path).path
        if path.startswith('/api/search'):
            self.handle_api_search()
            return

        elif self.path.startswith('/search'):
            self.handle_search()
            return

        elif self.path.startswith('/form'):
            self.handle_form()
            return

        elif path in APP_PATHS:
            self.serve_static('/index.html')
            return

        elif self.serve_static(path):
            return

        logging.info('Invalid path ' + self.path)
        self.handle_error(404, 'Not found')
        return

    def serve_static(self, path):
        """
            Serve a file from the static directory, returns False if not found
        """
        file_path = os.path.realpath(os.path.join(STATIC_DIR, path.lstrip('/')))
        if not file_path.startswith(STATIC_DIR + os.sep) or not os.path.isfile(file_path):
            return False

        extension = os.path.splitext(file_path)[1]
        extension_to_content_type = {
            '.js': 'application/javascript',
            '.json': 'application/json',
            '.webmanifest': 'application/manifest+json',
            '.html': 'text/html; charset=utf-8',
            '.svg': 'image/svg+xml',
            '.css': 'text/css',
            '.png': 'image/png',
        }
        if extension not in extension_to_content_type:
            return False

        with open(file_path, 'rb') as f:
            content = f.read()
        self.send_response(200)
        self.send_header('Content-type', extension_to_content_type[extension])
        self.send_header('Cache-Control', 'no-cache')
        if path == '/service-worker.js':
            self.send_header('Service-Worker-Allowed', '/')
        self.end_headers()
        self.wfile.write(content)
        return True


    def do_POST(self):
        """
            Handle POST request from client
        """
        logging.info('POST request')
        if self.path.startswith('/api/add'):
            self.handle_api_add()
            return

        if self.path.startswith('/add'):
            self.handle_add()
            return

        self.handle_error(404, 'Not found')

    def do_DELETE(self):
        """
            Handle DELETE request from client
        """
        if self.path.startswith('/api/remove'):
            self.handle_api_remove()
            return

        self.handle_error(404, 'Not found')

    def do_OPTIONS(self):
        """
            Handle OPTION request from client
        """
        logging.info('OPTION request')
        if self.path.startswith('/add'):
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
            return

        return

    def handle_form(self):
        
        form = """
        <form action="/add" method="post">
            <label for="url">Url</label>
            <input type="text" id="url" name="url" required>
            <label for="title">Title</label>
            <input type="text" id="title" name="title" required>
            <label for="category">Category</label>
            <input type="text" id="category" name="category" required>
            <input type="submit" value="Add">
        </form>

        """
        result = PAGE_TEMPLATE.format(form)
        # Send the result back to the client
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(bytes(result, 'utf-8'))


    def upstream(self, method, path, data=None, content_type=None):
        """
            Forward a request to the upstream bookmarks server and relay its JSON response
        """
        request = urllib.request.Request(BOOKMARKS_SERVER_URL + path, data=data, method=method)
        if content_type:
            request.add_header('Content-Type', content_type)
        logging.info('Upstream {} {}'.format(method, path))
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                status, body = response.status, response.read()
        except urllib.error.HTTPError as e:
            status, body = e.code, e.read()
        except (urllib.error.URLError, OSError) as e:
            logging.error('Upstream error: {}'.format(e))
            self.handle_error(502, 'Bookmarks server unavailable at {}'.format(BOOKMARKS_SERVER_URL))
            return

        try:
            json.loads(body)
        except ValueError:
            body = json.dumps({'error': 'Invalid response from bookmarks server'}).encode('utf-8')
            status = 502

        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get('Content-Length') or 0)
        try:
            return json.loads(self.rfile.read(length).decode('utf-8') or '{}')
        except ValueError:
            return None

    def handle_api_search(self):
        query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query).get('q', [''])[0]
        params = urllib.parse.urlencode({'q': query, 'format': 'json'})
        self.upstream('GET', '/search?' + params)

    def handle_api_add(self):
        body = self.read_json_body()
        if not isinstance(body, dict) or not str(body.get('url', '')).strip():
            self.handle_error(400, 'url is required')
            return

        url = str(body.get('url')).strip()
        tags = body.get('tags', '')
        if isinstance(tags, list):
            tags = ','.join(tags)
        # JSON rather than a form body: the upstream server does not URL-decode form fields
        data = json.dumps({
            'url': url,
            'title': str(body.get('title') or url).strip(),
            'category': str(body.get('category') or 'unsorted').strip(),
            'tags': str(tags).strip(),
        }).encode('utf-8')
        self.upstream('POST', '/add', data, 'application/json')

    def handle_api_remove(self):
        body = self.read_json_body()
        if not isinstance(body, dict) or not body.get('id'):
            self.handle_error(400, 'id is required')
            return

        data = json.dumps({'id': str(body.get('id'))}).encode('utf-8')
        self.upstream('DELETE', '/remove', data, 'application/json')

    def handle_error(self, code, message):
        """
            Handle error response
        """
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(bytes(json.dumps({'error': message}), 'utf-8'))

    def handle_search(self):
        """
            Handle search request from client
        """
        self.parse_params()
        search_value = self.get_params.get('q', '')
        format = self.get_params.get('format', 'html')
        logging.info('Searching for {}'.format(search_value))

        # search all the files in the directory tree using commandline
        command_dir = os.path.dirname(os.path.realpath(__file__))
        command = [command_dir + '/bookmarks', 'suggest', search_value]
        logging.info('Executing command: {}'.format(command))
        try:
            result = subprocess.check_output(command)
        except subprocess.CalledProcessError as e:
            logging.error('Error searching for {}'.format(search_value))
            self.output_result({'error': 'Error searching for {}'.format(search_value)}, 'json')
            return

        logging.debug('Result: {}'.format(result))
        # convert response text to json
        result = json.loads(result)
        self.output_result(result, format)

    def handle_add(self):
        """
            Handle add request from client
        """
        self.parse_params()
        url = self.post_params.get('url', '')
        title = self.post_params.get('title', '')
        category = self.post_params.get('category', '')
        logging.info('Adding {} {} {}'.format(url, title, category))

        # add a new bookmark using commandline
        command_dir = os.path.dirname(os.path.realpath(__file__))
        command = [command_dir + '/bookmarks', 'add', '--uri', url, '--title', title, '--category', category]
        logging.info('Executing command: {}'.format(command))
        # run the command in a subprocess and get the exit code
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        proc.wait()
        (stdout, stderr) = proc.communicate()

        if proc.returncode != 0:
            # if the exit code is not 0, then there was an error
            logging.error('Error adding url')
            # convert error message to json
            stderr = stderr.decode('utf-8')
            # split the error message into lines
            stderr = stderr.split('\n')
            # remove empty lines
            stderr = [line for line in stderr if line]
            self.output_result({'error': 'Error adding url', 'message': stderr}, 'json')
            return

        self.output_result({'success': 'Url added'}, 'json')

    def send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS, PUT, DELETE')
        self.send_header('Access-Control-Allow-Credentials', 'true')
        self.send_header('Access-Control-Max-Age', '86400')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')

    def output_result(self, result, format):
        """
            Output the result to the client
        """
        logging.info('Output format: {}'.format(format))
        if format == 'json':
            # Send the result back to the client
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_cors_headers()
            self.end_headers()
            # output json string
            self.wfile.write(bytes(json.dumps(result), 'utf-8'))
            return

        if format == 'text':
            # Send the result back to the client
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            # convert json to text
            result = '\n'.join([obj.get('url') for obj in result])
            self.wfile.write(bytes(str(result), 'utf-8'))

            return
        if format == 'html':
            # transform a list of uris to a html list of anchor tags
            result = ['<li><a href="{}">{}</a></li>'.format(o.get('title'), o.get('url')) for o in result]
            result = ''.join(result)
            result = '<ul>' + result + '</ul>'
            result = PAGE_TEMPLATE.format(result)
            # Send the result back to the client
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(result, 'utf-8'))

    def parse_params(self):
        """
            Parse the GET and POST parameters from the request
        """
        self.parse_get_params()
        self.parse_post_params()

    def parse_get_params(self):
        """
            Parse the GET parameters from the URL
        """
        # Parse the GET parameters
        self.get_params = {}
        if '?' in self.path:
            self.get_params = dict([p.split('=') for p in self.path.split('?')[1].split('&')])

        logging.info('GET path: {}'.format(self.path))
        logging.info('GET params: {}'.format(self.get_params))

    def parse_post_params(self):
        """
            Parse the POST parameters from the request body
        """
        # Parse the POST parameters
        self.post_params = {}
        if self.headers.get('Content-Length'):
            content_length = int(self.headers.get('Content-Length'))

            body = self.rfile.read(content_length)
            # parse json body
            if self.headers.get('Content-Type') == 'application/json':
                self.post_params = json.loads(body.decode('utf-8'))
            else:
                # parse url encoded body
                self.post_params = dict([p.split('=') for p in body.decode('utf-8').split('&')])

    def search_files(self, search_value):
        """
            Search all the files in the directory, and their contents for the search value
        """


# Get the port from the first commandline argument, and default to 8000 if missing
port = int(os.sys.argv[1]) if len(os.sys.argv) > 1 else 8000
server = Server(port)
server.run()

