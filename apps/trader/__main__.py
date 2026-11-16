"""Serve Kinn Trader: ``uv run python -m apps.trader [--strategy rebound_limit] [--port 8322]``.

Paper only. It listens on this computer alone and has no broker connection.
"""

from __future__ import annotations

import argparse
import json
from datetime import date
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from apps.trader.service import NoCandidate, Trader
from kinn.core.settings import load_settings

STATIC = Path(__file__).parent / "web" / "dist"


class Handler(SimpleHTTPRequestHandler):
    trader: Trader

    def do_GET(self):
        path = unquote(self.path.split("?")[0])
        if path == "/api/state":
            return self._json(self.trader.snapshot())
        if path == "/api/sessions":
            return self._json(self.trader.sessions())
        if path == "/api/days":
            return self._json(self.trader.suggested_days())
        if path.startswith("/api/sessions/"):
            found = self.trader.saved_session(path.rsplit("/", 1)[1])
            return self._json(found, 200 if found else 404)
        return super().do_GET()

    def do_POST(self):
        # Controls are for this page only: another site cannot set this header on a request.
        if self.headers.get("X-Kinn-Trader") != "1":
            return self._json({"error": "missing X-Kinn-Trader header"}, 403)
        length = int(self.headers.get("Content-Length") or 0)
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except json.JSONDecodeError:
            return self._json({"error": "the request body is not JSON"}, 400)
        path = self.path.split("?")[0]
        try:
            if path == "/api/replay":
                self.trader.start_replay(
                    date.fromisoformat(str(body.get("day"))),
                    seconds_per_minute=float(body.get("seconds_per_minute", 0.0)),
                )
            elif path == "/api/halt":
                self.trader.halt()
            elif path == "/api/resume":
                self.trader.resume()
            elif path == "/api/stop":
                self.trader.stop()
            else:
                return self._json({"error": "unknown control"}, 404)
        except (ValueError, RuntimeError) as error:
            return self._json({"error": str(error)}, 409)
        return self._json(self.trader.snapshot())

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
    parser.add_argument("--strategy", default="rebound_limit")
    parser.add_argument("--port", type=int, default=8322)
    args = parser.parse_args()
    if not (STATIC / "index.html").exists():
        raise SystemExit(
            "The Trader front end is not built yet. Run once:\n"
            "  cd apps/trader/web && npm install && npm run build"
        )
    try:
        Handler.trader = Trader(load_settings(), args.strategy)
    except NoCandidate as error:
        raise SystemExit(f"Nothing to trade: {error}") from error
    # 127.0.0.1 only: the controls must not be reachable from another machine.
    server = ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, directory=str(STATIC)))
    spec = Handler.trader.spec()
    print(f"Kinn Trader (paper) on http://127.0.0.1:{args.port}  "
          f"{spec['strategy']} {spec['config']}")  # fmt: skip
    server.serve_forever()


if __name__ == "__main__":
    main()
