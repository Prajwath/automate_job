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

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 5050
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Disable browser caching for CSV and HTML so real-time updates show immediately
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

def main():
    os.chdir(DIRECTORY)
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
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
