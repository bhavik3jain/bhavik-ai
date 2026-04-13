#!/usr/bin/env python3
"""
Scrum Master — local data server.

Serves the app HTML on GET /
Handles GET /data and POST /data for JSON persistence.
Data is stored at ~/.scrum-master/data.json

Usage:
    python server.py [--port PORT] [--data-dir DIR]
"""

import argparse
import json
import os
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DEFAULT_PORT = 4242
DEFAULT_DATA_DIR = Path.home() / ".scrum-master"

ASSETS_DIR = Path(__file__).parent.parent / "assets"


def get_html(port: int) -> bytes:
    html_path = ASSETS_DIR / "app.html"
    content = html_path.read_text(encoding="utf-8")
    # Inject the port so the frontend knows where to call
    content = content.replace("{{PORT}}", str(port))
    return content.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    data_file: Path = None  # set at startup

    def log_message(self, fmt, *args):  # silence default access log
        pass

    def _send(self, code: int, content_type: str, body: bytes):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self._send(204, "text/plain", b"")

    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            body = get_html(self.server.server_address[1])
            self._send(200, "text/html; charset=utf-8", body)

        elif self.path == "/data":
            if self.data_file.exists():
                data = self.data_file.read_bytes()
            else:
                data = b'{"items":[]}'
            self._send(200, "application/json", data)

        else:
            self._send(404, "text/plain", b"Not found")

    def do_POST(self):
        if self.path == "/data":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            # Validate JSON before writing
            try:
                json.loads(body)
            except json.JSONDecodeError:
                self._send(400, "text/plain", b"Invalid JSON")
                return
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self.data_file.write_bytes(body)
            self._send(200, "application/json", b'{"ok":true}')
        else:
            self._send(404, "text/plain", b"Not found")


def find_free_port(preferred: int) -> int:
    import socket
    for port in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found near", preferred)


def main():
    parser = argparse.ArgumentParser(description="Scrum Master local server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT,
                        help=f"Port to listen on (default {DEFAULT_PORT})")
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR,
                        help=f"Directory to store data (default {DEFAULT_DATA_DIR})")
    parser.add_argument("--no-browser", action="store_true",
                        help="Don't auto-open the browser")
    args = parser.parse_args()

    port = find_free_port(args.port)
    data_file = args.data_dir / "data.json"
    Handler.data_file = data_file

    server = HTTPServer(("localhost", port), Handler)
    url = f"http://localhost:{port}"

    print(f"[Scrum Master] Server running at {url}")
    print(f"[Scrum Master] Data stored at: {data_file}")
    print(f"[Scrum Master] Press Ctrl+C to stop.\n")

    if not args.no_browser:
        # Open browser after a short delay so server is ready
        def open_browser():
            import time
            time.sleep(0.4)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Scrum Master] Stopped.")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
