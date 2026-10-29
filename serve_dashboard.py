#!/usr/bin/env python3
"""
Simple local server for the Job Application & Outreach Tracker Dashboard.
Usage: python3 serve_dashboard.py [port]
"""
import http.server
import socketserver
import os
import sys
import webbrowser
from urllib.parse import urlsplit, unquote
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5050
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def allowed_path(self):
        path=unquote(urlsplit(self.path).path)
        if path in ('/', '/index.html', '/dashboard.html', '/job_applications.csv', '/favicon.ico'):
            return True
        base=Path(DIRECTORY)/'output/pdf'
        target=(Path(DIRECTORY)/path.lstrip('/')).resolve()
        return path.startswith('/output/pdf/') and target.is_relative_to(base.resolve()) and target.suffix=='.pdf' and target.is_file()

    def do_GET(self):
        if not self.allowed_path():
            self.send_error(404)
            return
        super().do_GET()

    def do_HEAD(self):
        if not self.allowed_path():
            self.send_error(404)
            return
        super().do_HEAD()

    def end_headers(self):
        # Disable browser caching for CSV and HTML so real-time updates show immediately
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def main():
    os.chdir(DIRECTORY)
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Handler) as httpd:
        url = f"http://localhost:{PORT}/dashboard.html"
        print("=" * 60)
        print(f" Job Application Tracker Dashboard running at:")
        print(f" ==> {url}")
        print("=" * 60)
        print("Press Ctrl+C to stop the server.\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")

if __name__ == "__main__":
    main()
