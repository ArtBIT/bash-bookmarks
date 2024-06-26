#!/usr/bin/env python3
"""
    Create simple HTTP server to handle requests from client, get the
    search value, use it to fuzzy search the files in the directory and
    send back the results to the client
"""

import os
import json
import logging
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

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
        httpd = HTTPServer(server_address, ServerHandler)
        httpd.serve_forever()

class ServerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """
            Handle GET request from client
        """
        static_dir = os.path.dirname(os.path.realpath(__file__)) + '/static'
        if self.path.startswith('/search'):
            self.handle_search()
            return

        elif self.path.startswith('/form'):
            self.handle_form()
            return

        elif os.path.exists(static_dir + self.path) and os.path.isfile(static_dir + self.path):
            extension = os.path.splitext(self.path)[1]
            extension_to_content_type = {
                '.js': 'application/javascript',
                '.json': 'application/json',
                '.html': 'text/html',
                '.svg': 'image/svg+xml',
                '.css': 'text/css',
                '.png': 'image/png',
            }
            if extension not in extension_to_content_type:
                self.handle_error(404, 'Invalid extension ' + extension)
                return

            self.send_response(200)
            self.send_header('Content-type', extension_to_content_type[extension])
            self.end_headers()

            binary_extensions = ['.png', '.jpg', '.jpeg', '.gif', '.ico', '.svg', '.woff', '.woff2', '.ttf', '.eot', '.otf']
            if extension in binary_extensions:
                with open(static_dir + self.path, 'rb') as f:
                    self.wfile.write(f.read())
                return
            else:
                with open(static_dir + self.path, 'r') as f:
                    self.wfile.write(bytes(f.read(), 'utf-8'))
            return

        elif self.path == '/' or self.path == '':
            result = PAGE_TEMPLATE.format('Go to <a href="https://github.com/ArtBIT/bash-bookmarks">Bash bookmarks</a> for more info.')
            # Send the result back to the client
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(bytes(result, 'utf-8'))
            return

        logging.info('Invalid path ' + self.path)
        return

    def do_POST(self):
        """
            Handle POST request from client
        """
        logging.info('POST request')
        if self.path.startswith('/add'):
            self.handle_add()
            return

        return

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

