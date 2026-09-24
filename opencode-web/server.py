#!/usr/bin/env python3
"""
OpenCode Web Client Runner
Zero-dependency HTTP server with static serving and optional reverse proxy.
"""

import sys
import os
import argparse
import urllib.request
import urllib.error
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

OPENCODE_DEFAULT_URL = "http://127.0.0.1:4096"

class OpenCodeProxyHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, directory=None, target_url=OPENCODE_DEFAULT_URL, **kwargs):
        self.target_url = target_url.rstrip("/")
        super().__init__(*args, directory=directory, **kwargs)

    def end_headers(self):
        # Enable CORS for convenience
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS, PATCH")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    def _is_proxy_route(self):
        # Forward API and session requests to opencode backend if called via proxy path
        p = self.path.split("?")[0]
        return p.startswith("/api/") or p.startswith("/session") or p == "/event" or p == "/provider"

    def do_GET(self):
        if self._is_proxy_route():
            self._proxy_request("GET")
        else:
            super().do_GET()

    def do_POST(self):
        if self._is_proxy_route():
            self._proxy_request("POST")
        else:
            self.send_error(404, "Not Found")

    def do_DELETE(self):
        if self._is_proxy_route():
            self._proxy_request("DELETE")
        else:
            self.send_error(404, "Not Found")

    def _proxy_request(self, method):
        target = f"{self.target_url}{self.path}"
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else None

        req = urllib.request.Request(target, data=body, method=method)
        for header, value in self.headers.items():
            if header.lower() not in ("host", "content-length"):
                req.add_header(header, value)

        try:
            with urllib.request.urlopen(req, timeout=120) as response:
                self.send_response(response.status)
                for h, val in response.headers.items():
                    if h.lower() not in ("content-length", "transfer-encoding"):
                        self.send_header(h, val)
                data = response.read()
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for h, val in e.headers.items():
                if h.lower() not in ("content-length", "transfer-encoding"):
                    self.send_header(h, val)
            data = e.read()
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(f'{{"error": "Proxy Error: {str(e)}"}}'.encode())


def check_opencode_health(url):
    try:
        with urllib.request.urlopen(f"{url.rstrip('/')}/api/health", timeout=1.5) as r:
            return r.status == 200
    except Exception:
        try:
            with urllib.request.urlopen(f"{url.rstrip('/')}/session", timeout=1.5) as r:
                return r.status == 200
        except Exception:
            return False


def main():
    parser = argparse.ArgumentParser(description="Run OpenCode Web Client")
    parser.add_argument("--port", type=int, default=3000, help="Port to serve web client on (default: 3000)")
    parser.add_argument("--opencode-url", type=str, default=OPENCODE_DEFAULT_URL, help="OpenCode backend URL")
    args = parser.parse_args()

    web_dir = os.path.dirname(os.path.abspath(__file__))

    print("=" * 60)
    print(" ⚡ OpenCode Custom Web Client")
    print("=" * 60)

    # Health check on OpenCode
    print(f"[*] Checking OpenCode backend at {args.opencode_url} ...", end=" ", flush=True)
    if check_opencode_health(args.opencode_url):
        print("\033[92mONLINE\033[0m")
    else:
        print("\033[93mNOT DETECTED\033[0m")
        print("    [!] Make sure 'opencode web' or 'opencode serve' is running.")

    handler_factory = lambda *h_args, **h_kwargs: OpenCodeProxyHandler(
        *h_args, directory=web_dir, target_url=args.opencode_url, **h_kwargs
    )

    try:
        server = ThreadingHTTPServer(("0.0.0.0", args.port), handler_factory)
    except OSError as e:
        print(f"\n[!] Failed to bind port {args.port}: {e}")
        print("    Try using another port: python3 server.py --port 8080")
        sys.exit(1)

    print(f"[*] Web Client URL: \033[94mhttp://localhost:{args.port}\033[0m")
    print(f"[*] Serving files from: {web_dir}")
    print("[*] Press Ctrl+C to stop.")
    print("=" * 60)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Stopping server...")
        server.server_close()
        print("[*] Done.")


if __name__ == "__main__":
    main()
