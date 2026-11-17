"""Serve the Workbench: ``uv run python -m apps.workbench [--port 8321]``."""

from __future__ import annotations

import argparse
import json
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

import yaml

from apps.workbench import api, record
from kinn import swing_paper, swing_run
from kinn.core.settings import load_settings
from kinn.run import strategies_dir

STATIC = Path(__file__).parent / "web" / "dist"


class Handler(SimpleHTTPRequestHandler):
    runs_dir: Path

    def do_GET(self):
        path = unquote(self.path.split("?")[0])
        if path == "/api/runs":
            return self._json(api.list_runs(self.runs_dir))
        if path == "/api/families":
            return self._json(api.families(self.runs_dir))
        if path == "/api/strategies":
            return self._json(api.strategies(self.runs_dir, strategies_dir()))
        if path.startswith("/api/runs/"):
            detail = api.run_detail(self.runs_dir, path.rsplit("/", 1)[1])
            return self._json(detail, 200 if detail else 404)
        if path == "/api/board":
            return self._json(record.board(self.runs_dir, strategies_dir()))
        if path == "/api/studies":
            return self._json(record.studies(strategies_dir()))
        if path.startswith("/api/strategy/"):
            parts = path.split("/")[3:]
            if len(parts) == 2 and parts[1] == "documents":
                found = record.documents(strategies_dir(), parts[0])
            elif len(parts) == 2 and parts[1] == "paper":
                found = self._paper(parts[0])
            else:
                found = record.strategy_page(self.runs_dir, strategies_dir(), parts[0])
            return self._json(found, 200 if found else 404)
        if path.startswith("/api/trades/"):
            found = record.trades(self.runs_dir, path.rsplit("/", 1)[1])
            return self._json(found, 200 if found else 404)
        if path == "/api/info":
            return self._json({"runs_dir": str(self.runs_dir)})
        return super().do_GET()

    def _paper(self, name: str):
        """The paper ledger of a strategy that names one in its record."""
        if not record.NAME.match(name):
            return None
        try:
            _, cfg = swing_run.load_config(name, "paper")
        except (FileNotFoundError, yaml.YAMLError):
            return None
        folder = swing_paper.paper_dir(self.runs_dir, name)
        hold = int((cfg.get("rule") or {}).get("hold") or 0) or None
        return record.paper(folder, cfg.get("books"), hold)

    def _json(self, payload, status=200):
        body = json.dumps(payload, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def end_headers(self):
        # The page itself is always re-checked, so a rebuild shows without a hard refresh.
        # Files under /assets/ carry a hash in their name and may be cached.
        if not self.path.startswith(("/assets/", "/api/")):
            self.send_header("Cache-Control", "no-cache")
        super().end_headers()

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
