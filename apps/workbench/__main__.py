"""Serve the Workbench: ``uv run python -m apps.workbench [--port 8321]``."""

from __future__ import annotations

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from apps.workbench import api
from kinn.core.settings import load_settings

STATIC = Path(__file__).parent / "web" / "dist"


class Handler(SimpleHTTPRequestHandler):
    runs_dir: Path

    def do_GET(self):
        path = unquote(self.path.split("?")[0])
        if path == "/api/runs":
            return self._json(api.list_runs(self.runs_dir))
        if path == "/api/families":
            return self._json(api.families(self.runs_dir))
        if path.startswith("/api/runs/"):
            detail = api.run_detail(self.runs_dir, path.rsplit("/", 1)[1])
            return self._json(detail, 200 if detail else 404)
        if path == "/api/info":
            return self._json({"runs_dir": str(self.runs_dir)})
        return super().do_GET()

    def _json(self, payload, status=200):
        body = json.dumps(payload, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8321)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()
    if not (STATIC / "index.html").exists():
        raise SystemExit(
            "The Workbench front end is not built yet. Run once:\n"
            "  cd apps/workbench/web && npm install && npm run build"
        )
    Handler.runs_dir = load_settings().runs_dir
    server = ThreadingHTTPServer((args.host, args.port), partial(Handler, directory=str(STATIC)))
    print(f"Workbench on http://{args.host}:{args.port}  (runs: {Handler.runs_dir})")
    server.serve_forever()


if __name__ == "__main__":
    main()
