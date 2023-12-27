"""
    Create simple HTTP server to handle requests from client, get the
    search value, use it to fuzzy search the files in the directory and
    send back the results to the client
"""

import os
import json
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Bookmarks</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@picocss/pico@1/css/pico.min.css" />
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
        server_address = ('', self.port)
        httpd = HTTPServer(server_address, ServerHandler)
        print('Server running on port {}'.format(self.port))
        httpd.serve_forever()

class ServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
            Handle GET request from client
        """
        if self.path.startswith('/search'):
            self.handle_search()
            return
        print('Invalid path')
        return

    def do_POST(self):
        """
            Handle POST request from client
        """
        print('POST request')
        if self.path.startswith('/add'):
            self.handle_add()
            return

        return

    def do_OPTIONS(self):
        """
            Handle OPTION request from client
        """
        print('OPTION request')
        if self.path.startswith('/add'):
            self.send_response(200)
            self.send_cors_headers()
            self.end_headers()
            return

        return

    def handle_search(self):
        """
            Handle search request from client
        """
        self.parse_params()
        search_value = self.get_params.get('q', '')
        format = self.get_params.get('format', 'html')
        print('Searching for {}'.format(search_value))

        # search all the files in the directory tree using commandline
        command_dir = os.path.dirname(os.path.realpath(__file__))
        command = [command_dir + '/bookmarks', 'suggest', search_value]
        print('Executing command: {}'.format(command))
        result = subprocess.check_output(command)

        print('Result: {}'.format(result))
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
        print('Adding {} {} {}'.format(url, title, category))

        # add a new bookmark using commandline
        command_dir = os.path.dirname(os.path.realpath(__file__))
        command = [command_dir + '/bookmarks', 'add', '--uri', url, '--title', title, '--category', category]
        print('Executing command: {}'.format(command))
        # run the command in a subprocess and get the exit code
        exit_code = subprocess.call(command)

        if exit_code != 0:
            # if the exit code is not 0, then there was an error
            print('Error adding url')
            self.output_result({'error': 'Error adding url'}, 'json')
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

