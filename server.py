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
        if not self.path.startswith('/search'):
            print('Invalid path')
            return
        # Parse the GET parameters
        self.parse_get_params()
        search_value = self.get_params.get('q', '')
        format = self.get_params.get('format', 'html')
        print('Searching for {}'.format(search_value))
        # Search the files in the directory
        result = self.search_files(search_value)
        print('Result: {}'.format(result))
        # convert response text to json
        result = json.loads(result)


        if format == 'json':
            # Send the result back to the client
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
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

    def parse_get_params(self):
        """
            Parse the GET parameters from the URL
        """
        # Parse the GET parameters
        self.get_params = {}
        if '?' in self.path:
            self.get_params = dict([p.split('=') for p in self.path.split('?')[1].split('&')])

    def search_files(self, search_value):
        """
            Search all the files in the directory, and their contents for the search value
        """
        # search all the files in the directory tree using commandline
        command_dir = os.path.dirname(os.path.realpath(__file__))
        command = [command_dir + '/bookmarks', 'suggest', search_value]
        print('Executing command: {}'.format(command))
        return subprocess.check_output(command)


# Get the port from the first commandline argument, and default to 8000 if missing
port = int(os.sys.argv[1]) if len(os.sys.argv) > 1 else 8000
server = Server(port)
server.run()

