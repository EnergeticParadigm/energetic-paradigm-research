#!/usr/bin/env python3
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

UI_ROOT = Path("/Users/wesleyshu/ep_system/ep_api_system/ep_verified_ui_3000")
INDEX_FILE = UI_ROOT / "index.html"
API_BASE = "http://127.0.0.1:8000"
HOST = "127.0.0.1"
PORT = 3000

def backend_call(method: str, path: str, payload=None, timeout=60):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(
        url=f"{API_BASE}{path}",
        data=data,
        headers=headers,
        method=method,
    )
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl.create_default_context()) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
            return resp.getcode(), latency_ms, body
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="ignore")
        except Exception:
            body = str(e)
        latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
        return e.code, latency_ms, body
    except Exception as e:
        latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
        return 502, latency_ms, json.dumps({"status": "error", "detail": str(e)})

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def send_bytes(self, code: int, data: bytes, content_type: str):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def send_text(self, code: int, text: str, content_type: str = "text/plain; charset=utf-8"):
        self.send_bytes(code, text.encode("utf-8", errors="ignore"), content_type)

    def send_json(self, code: int, obj):
        self.send_text(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

    def do_GET(self):
        if self.path == "/" or self.path.startswith("/?"):
            self.send_text(200, INDEX_FILE.read_text(encoding="utf-8", errors="ignore"), "text/html; charset=utf-8")
            return

        if self.path == "/api/health":
            code, latency_ms, body = backend_call("GET", "/v1/ep/health", None, 20)
            data = body.encode("utf-8", errors="ignore")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Backend-Latency-Ms", str(latency_ms))
            self.end_headers()
            self.wfile.write(data)
            return

        if self.path == "/api/openapi":
            code, latency_ms, body = backend_call("GET", "/openapi.json", None, 20)
            data = body.encode("utf-8", errors="ignore")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Backend-Latency-Ms", str(latency_ms))
            self.end_headers()
            self.wfile.write(data)
            return

        self.send_json(404, {"status": "error", "detail": "Not Found"})

    def do_POST(self):
        if self.path not in {"/api/respond", "/api/analyze"}:
            self.send_json(404, {"status": "error", "detail": "Not Found"})
            return

        content_length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(content_length) if content_length > 0 else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8", errors="ignore"))
        except Exception:
            self.send_json(400, {"status": "error", "detail": "Invalid JSON"})
            return

        route = "/v1/ep/respond" if self.path == "/api/respond" else "/v1/ep/analyze"
        code, latency_ms, body = backend_call("POST", route, payload, 90)
        data = body.encode("utf-8", errors="ignore")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Backend-Latency-Ms", str(latency_ms))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):
        return

if __name__ == "__main__":
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.serve_forever()
