#!/usr/bin/env python3
"""
API Lite — local HTTP server.

GET  /               → serves app.html
GET  /data           → returns saved state (collections + history + environments)
POST /data           → persists state
GET  /postman-collections → scans Postman app data dirs and returns found collections
POST /proxy          → executes an HTTP request on behalf of the browser (avoids CORS)

Usage:
    python3 server.py [--port PORT] [--data-dir DIR] [--no-browser]
"""

import argparse
import json
import os
import socket
import ssl
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

DEFAULT_PORT = 4747
DEFAULT_DATA_DIR = Path.home() / ".api-lite"
ASSETS_DIR = Path(__file__).parent.parent / "assets"

# Common Postman data directories across platforms
POSTMAN_SEARCH_PATHS = [
    Path.home() / "Library" / "Application Support" / "Postman" / "IndexedDB",
    Path.home() / "Library" / "Application Support" / "Postman",
    Path.home() / ".config" / "Postman",
    Path.home() / "AppData" / "Roaming" / "Postman",
]


def get_html(port: int) -> bytes:
    html_path = ASSETS_DIR / "app.html"
    content = html_path.read_text(encoding="utf-8")
    content = content.replace("{{PORT}}", str(port))
    return content.encode("utf-8")


def scan_postman_collections() -> list:
    """Walk known Postman data dirs and find collection JSON files."""
    collections = []

    # Postman stores collections as JSON files — look for them recursively
    for search_path in POSTMAN_SEARCH_PATHS:
        if not search_path.exists():
            continue
        try:
            for p in search_path.rglob("*.json"):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    if len(text) < 20:
                        continue
                    data = json.loads(text)
                    # Postman collection v2.x has info.schema containing "collection"
                    info = data.get("info") or data.get("Info")
                    if isinstance(info, dict):
                        schema = info.get("schema", "")
                        if "collection" in schema.lower():
                            collections.append({
                                "path": str(p),
                                "name": info.get("name", p.stem),
                                "schema": schema,
                                "data": data,
                            })
                            continue
                    # Postman v1 format
                    if "requests" in data and "id" in data and "name" in data:
                        collections.append({
                            "path": str(p),
                            "name": data.get("name", p.stem),
                            "schema": "v1",
                            "data": data,
                        })
                except (json.JSONDecodeError, PermissionError, OSError):
                    continue
        except PermissionError:
            continue

    return collections


def execute_request(payload: dict) -> dict:
    """
    Execute an HTTP request described by payload and return the result.

    payload keys:
        method, url, headers (dict), body (str|None), timeout (int, default 30)
    """
    method = payload.get("method", "GET").upper()
    url = payload.get("url", "")
    headers = payload.get("headers") or {}
    body = payload.get("body")
    timeout = int(payload.get("timeout") or 30)

    if not url:
        return {"error": "url is required"}

    body_bytes = body.encode("utf-8") if isinstance(body, str) else (body or None)

    req = urllib.request.Request(url, data=body_bytes, method=method)
    for k, v in headers.items():
        req.add_header(k, v)

    ssl_ctx = ssl._create_unverified_context()

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_ctx) as resp:
            elapsed_ms = int((time.time() - start) * 1000)
            resp_body = resp.read()
            resp_headers = dict(resp.headers)
            status = resp.status
            try:
                resp_text = resp_body.decode("utf-8")
            except UnicodeDecodeError:
                resp_text = resp_body.decode("latin-1")
            return {
                "status": status,
                "statusText": resp.reason,
                "headers": resp_headers,
                "body": resp_text,
                "elapsed_ms": elapsed_ms,
                "size_bytes": len(resp_body),
            }
    except urllib.error.HTTPError as e:
        elapsed_ms = int((time.time() - start) * 1000)
        try:
            error_body = e.read().decode("utf-8", errors="replace")
        except Exception:
            error_body = ""
        return {
            "status": e.code,
            "statusText": e.reason,
            "headers": dict(e.headers),
            "body": error_body,
            "elapsed_ms": elapsed_ms,
            "size_bytes": len(error_body),
        }
    except urllib.error.URLError as e:
        return {"error": str(e.reason)}
    except Exception as e:
        return {"error": str(e)}


class Handler(BaseHTTPRequestHandler):
    data_file: Path = None

    def log_message(self, fmt, *args):
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

    def _json(self, code: int, obj):
        body = json.dumps(obj).encode("utf-8")
        self._send(code, "application/json", body)

    def do_OPTIONS(self):
        self._send(204, "text/plain", b"")

    def do_GET(self):
        path = self.path.split("?")[0]

        if path in ("/", "/index.html"):
            body = get_html(self.server.server_address[1])
            self._send(200, "text/html; charset=utf-8", body)

        elif path == "/data":
            if self.data_file.exists():
                self._send(200, "application/json", self.data_file.read_bytes())
            else:
                self._json(200, {"collections": [], "history": [], "environments": [], "activeEnv": None})

        elif path == "/postman-collections":
            try:
                cols = scan_postman_collections()
                self._json(200, {"collections": cols})
            except Exception as e:
                self._json(500, {"error": str(e)})

        else:
            self._send(404, "text/plain", b"Not found")

    def do_POST(self):
        path = self.path.split("?")[0]
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        if path == "/data":
            try:
                json.loads(raw)
            except json.JSONDecodeError:
                self._send(400, "text/plain", b"Invalid JSON")
                return
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self.data_file.write_bytes(raw)
            self._json(200, {"ok": True})

        elif path == "/proxy":
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                self._json(400, {"error": "Invalid JSON payload"})
                return
            result = execute_request(payload)
            self._json(200, result)

        else:
            self._send(404, "text/plain", b"Not found")


def find_free_port(preferred: int) -> int:
    for port in range(preferred, preferred + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"No free port found near {preferred}")


def main():
    parser = argparse.ArgumentParser(description="API Lite local server")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA_DIR)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    port = find_free_port(args.port)
    Handler.data_file = args.data_dir / "data.json"

    server = HTTPServer(("localhost", port), Handler)
    url = f"http://localhost:{port}"

    print(f"[API Lite] Server running at {url}")
    print(f"[API Lite] Data stored at: {Handler.data_file}")
    print(f"[API Lite] Press Ctrl+C to stop.\n")

    if not args.no_browser:
        def open_browser():
            time.sleep(0.4)
            webbrowser.open(url)
        threading.Thread(target=open_browser, daemon=True).start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[API Lite] Stopped.")
        server.server_close()
        sys.exit(0)


if __name__ == "__main__":
    main()
