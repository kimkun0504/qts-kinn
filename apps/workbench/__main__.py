"""Serve the Workbench: ``uv run python -m apps.workbench [--port 8321]``."""

from __future__ import annotations

import argparse
import gzip
import hmac
import json
import secrets
import threading
from datetime import date
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlsplit

import yaml

from apps.workbench import api, catalog, lab, ledgers, markets, record, screener, stocks
from kinn import swing_paper, swing_run
from kinn.core.settings import load_settings
from kinn.data.store import DataStore
from kinn.lab import store as lab_store
from kinn.run import REPO_ROOT, strategies_dir

GUIDES = {
    "lab": REPO_ROOT / "docs" / "LAB.md",
    "workbench": REPO_ROOT / "apps" / "workbench" / "README.md",
}

STATIC = Path(__file__).parent / "web" / "dist"
LOOPBACK = ("127.0.0.1", "localhost", "::1")
DEV_PORT = 5173  # Vite's dev server, which proxies /api here
MAX_BODY = 1_000_000  # bytes
LAB_OFF = ("The Lab is off: the Workbench listens beyond this machine. Start it without --host "
           "to use the Lab.")  # fmt: skip


class Handler(SimpleHTTPRequestHandler):
    runs_dir: Path
    lab_dir: Path
    port: int = 8321
    token: str = ""  # made at start; the page reads it from /api/lab/session
    lab_enabled: bool = True  # only when the server listens on this machine alone

    # -- the Lab: checks first ------------------------------------------------------------
    def _host_ok(self) -> bool:
        """The Host header names this machine (stops DNS rebinding)."""
        host = (self.headers.get("Host") or "").strip().lower()
        allowed = {f"{name}:{port}" for name in ("127.0.0.1", "localhost", "[::1]")
                   for port in (self.port, DEV_PORT)}  # fmt: skip
        return host in allowed

    def _origin_ok(self) -> bool:
        """A write comes from the Workbench's own page (or the dev server), never another site."""
        origin = self.headers.get("Origin")
        if origin is None:  # not a browser cross-site request (curl, tests)
            return True
        allowed = {f"http://{name}:{port}" for name in ("127.0.0.1", "localhost", "[::1]")
                   for port in (self.port, DEV_PORT)}  # fmt: skip
        return origin.lower() in allowed

    def _lab(self, method: str) -> None:
        if not self.lab_enabled:
            return self._json({"error": LAB_OFF}, 403)
        if not self._host_ok():
            return self._json({"error": "Use the Workbench at 127.0.0.1 or localhost."}, 403)
        split = urlsplit(self.path)
        parts = [unquote(p) for p in split.path[len("/api/lab/") :].split("/") if p]
        query = parse_qs(split.query)
        if method == "GET" and parts == ["session"]:
            return self._json({"token": self.token})
        if method == "GET" and len(parts) == 3 and parts[0] == "runs" and parts[2] == "trades.csv":
            status, text = lab.trades_csv(self.lab_dir, parts[1])
            return self._text(text, status, "text/csv; charset=utf-8",
                              f"{parts[1]}_trades.csv" if status == 200 else None)  # fmt: skip
        body = None
        if method != "GET":
            sent = self.headers.get("X-Kinn-Token") or ""
            if not self._origin_ok() or not hmac.compare_digest(sent, self.token):
                return self._json({"error": "This request did not come from the Workbench "
                                   "page. Reload the page."}, 403)  # fmt: skip
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                return self._json({"error": "Bad Content-Length."}, 400)
            if length > MAX_BODY:
                return self._json({"error": "The request is too large."}, 413)
            if length:
                if "application/json" not in (self.headers.get("Content-Type") or ""):
                    return self._json({"error": "Send JSON."}, 415)
                try:
                    body = json.loads(self.rfile.read(length))
                except (ValueError, UnicodeDecodeError):
                    return self._json({"error": "The body is not valid JSON."}, 400)
                if not isinstance(body, dict):
                    return self._json({"error": "The body must be a JSON object."}, 400)
        status, payload = lab.route(method, parts, query, body, self.lab_dir)
        return self._json(payload, status)

    def do_POST(self):
        if self.path.startswith("/api/lab/"):
            return self._lab("POST")
        return self._json({"error": "Not found."}, 404)

    def do_PUT(self):
        if self.path.startswith("/api/lab/"):
            return self._lab("PUT")
        return self._json({"error": "Not found."}, 404)

    def do_DELETE(self):
        if self.path.startswith("/api/lab/"):
            return self._lab("DELETE")
        return self._json({"error": "Not found."}, 404)

    def do_GET(self):
        if self.path.startswith("/api/lab/"):
            return self._lab("GET")
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
        if path == "/api/compare":
            wanted = parse_qs(urlsplit(self.path).query).get("ids", [""])[0].split(",")
            return self._json(api.compare(self.runs_dir, wanted))
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
        if path == "/api/data":
            store = self._store()
            if store is None:
                return self._json({"error": "No data build."}, 503)
            return self._json(catalog.catalog(load_settings(), store))
        if path == "/api/stocks":
            store = self._store()
            query = parse_qs(urlsplit(self.path).query).get("q", [""])[0]
            return self._json(stocks.search(store, query) if store else [])
        if path.startswith("/api/stock/"):
            store = self._store()
            if store is None:
                return self._json({"error": "No data build to read prices from."}, 503)
            query = parse_qs(urlsplit(self.path).query)
            pick = query.get("pt", [""])[0]
            try:
                on = date.fromisoformat(query.get("on", [""])[0])
            except ValueError:
                on = None
            found = stocks.stock(store, self.runs_dir, self.lab_dir, path.rsplit("/", 1)[1],
                                 int(pick) if pick.isdigit() else None, on)  # fmt: skip
            return self._json(found, 200 if found else 404)
        if path.startswith("/api/guide/"):
            found = GUIDES.get(path.rsplit("/", 1)[1])
            if found is None or not found.exists():
                return self._json({"error": "No such guide."}, 404)
            return self._json({"name": found.name, "text": found.read_text()})
        if path == "/api/markets":
            store = self._store()
            if store is None:
                return self._json({"error": "No data build to read prices from."}, 503)
            try:
                on = date.fromisoformat(parse_qs(urlsplit(self.path).query).get("on", [""])[0])
            except ValueError:
                on = None
            try:
                return self._json(markets.markets(store, on))
            except ValueError as error:
                return self._json({"error": str(error)}, 404)
        if path == "/api/closes":
            store = self._store()
            if store is None:
                return self._json({"error": "No data build to read prices from."}, 503)
            wanted = parse_qs(urlsplit(self.path).query).get("symbols", [""])[0].split(",")
            return self._json(stocks.closes(store, wanted))
        if path == "/api/screen/ahead":
            store = self._store()
            if store is None:
                return self._json({"error": "No data build to screen."}, 503)
            try:
                on = date.fromisoformat(parse_qs(urlsplit(self.path).query).get("on", [""])[0])
                return self._json(screener.ahead(store, on))
            except ValueError as error:
                return self._json({"error": str(error)}, 400)
        if path == "/api/screen":
            store = self._store()
            if store is None:
                return self._json({"error": "No data build to screen."}, 503)
            try:
                on = date.fromisoformat(parse_qs(urlsplit(self.path).query).get("on", [""])[0])
            except ValueError:
                on = None
            try:
                return self._json(screener.screen(store, on))
            except ValueError as error:
                return self._json({"error": str(error)}, 404)
        if path == "/api/ledgers":
            return self._json(ledgers.ledgers(self.runs_dir))
        if path.startswith("/api/ledgers/"):
            found = ledgers.ledger(self.runs_dir, path.rsplit("/", 1)[1])
            return self._json(found, 200 if found else 404)
        if path == "/api/info":
            return self._json({"runs_dir": str(self.runs_dir)})
        return super().do_GET()

    def _store(self):
        try:
            return DataStore(load_settings())
        except (FileNotFoundError, KeyError, OSError, ValueError):
            return None

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

    def _text(self, text: str, status: int, kind: str, filename: str | None = None):
        body = text.encode()
        self.send_response(status)
        self.send_header("Content-Type", kind)
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload, status=200):
        body = json.dumps(payload, default=str).encode()
        packed = len(body) > 32_768 and "gzip" in self.headers.get("Accept-Encoding", "")
        if packed:
            body = gzip.compress(body, compresslevel=5)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        if packed:
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Vary", "Accept-Encoding")
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
    settings = load_settings()
    Handler.runs_dir = settings.runs_dir
    Handler.lab_dir = lab_store.lab_dir(settings)
    Handler.port = args.port
    Handler.token = secrets.token_urlsafe(32)
    Handler.lab_enabled = args.host in LOOPBACK
    server = ThreadingHTTPServer((args.host, args.port), partial(Handler, directory=str(STATIC)))
    print(f"Workbench on http://{args.host}:{args.port}  (runs: {Handler.runs_dir})")
    if Handler.lab_enabled:
        print(f"Lab folder: {Handler.lab_dir}")
        threading.Thread(target=lab.keep_dispatching, args=(Handler.lab_dir,), daemon=True,
                         name="lab-queue").start()  # fmt: skip
    else:
        print("The Lab is off: it runs code, so it serves only on 127.0.0.1 or localhost.")
    server.serve_forever()


if __name__ == "__main__":
    main()
