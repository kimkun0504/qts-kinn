"""The Lab's endpoints and the server's checks on them (decision 0023)."""

from __future__ import annotations

import http.client
import json
import os
import threading
from functools import partial
from http.server import ThreadingHTTPServer

import pytest

from apps.workbench import lab
from apps.workbench.__main__ import Handler
from kinn.lab import runner, store
from tests.lab_fake import standard

PERIOD = {
    "period": "custom",
    "start": "2015-01-02",
    "end": "2015-09-30",
    "universe": {"min_market_cap": 1e6},
}
CODE = '''"""Two up days."""
SETTINGS = {"exit": {"hold_days": 5}}

def signal(data):
    up = data.returns > 0
    return up & up.shift(1, fill_value=False)
'''


@pytest.fixture(scope="module")
def fake():
    return standard()


@pytest.fixture
def root(tmp_path):
    return tmp_path / "lab"


@pytest.fixture
def finished(root, fake):
    """A Lab with one finished run (run in-process on the fake store)."""
    launch = partial(runner.run, open_store=lambda: fake)
    status, payload = lab.route(
        "POST",
        ["runs"],
        {},
        {"algorithm": "two-up", "code": CODE, "settings": PERIOD},
        root,
        launch,
    )
    assert status == 202, payload
    return payload["run_id"]


def get(root, *parts, **query):
    return lab.route("GET", list(parts), {k: [str(v)] for k, v in query.items()}, None, root)


# -- endpoints ----------------------------------------------------------------------------
def test_settings_are_read_from_the_code_without_running_it():
    assert lab.literal_settings(CODE) == {"exit": {"hold_days": 5}}
    assert lab.literal_settings("SETTINGS = make()\n") is None
    assert lab.literal_settings("SETTINGS: dict = {'book': {'max_positions': 3}}") == {
        "book": {"max_positions": 3}
    }
    assert lab.literal_settings("def (") is None
    assert lab.literal_settings("import os\nos.system('x')\n") is None


def test_meta_lists_fields_periods_and_defaults(root):
    status, meta = get(root, "meta")
    assert status == 200 and meta["active_run"] is None
    assert {"close", "trade_size", "revenue"} <= {f["name"] for f in meta["fields"]}
    assert [p["name"] for p in meta["periods"]][:2] == ["search", "early"]
    assert meta["defaults"]["exit"]["hold_days"] == 20


def test_save_read_and_delete_an_algorithm(root):
    assert lab.route("PUT", ["algorithms", "mine"], {}, {"code": CODE}, root)[0] == 200
    status, found = get(root, "algorithms", "mine")
    assert status == 200 and found["code"] == CODE and found["settings_in_code"]
    assert get(root, "algorithms")[1][0]["name"] == "mine"
    assert lab.route("DELETE", ["algorithms", "mine"], {}, None, root)[0] == 200
    assert get(root, "algorithms", "mine")[0] == 404
    assert lab.route("PUT", ["algorithms", "Bad Name"], {}, {"code": CODE}, root)[0] == 400


def test_a_bad_setting_is_refused_before_a_run_is_made(root):
    status, payload = lab.route(
        "POST",
        ["runs"],
        {},
        {"algorithm": "x", "code": CODE, "settings": {"exit": {"hold_days": 999}}},
        root,
        launch=lambda run_dir: pytest.fail("no run should start"),
    )
    assert status == 400 and "exit.hold_days" in payload["error"]
    assert get(root, "runs")[1] == []


def test_a_run_and_its_results(root, finished):
    status, detail = get(root, "runs", finished)
    assert status == 200 and detail["status"]["state"] == "complete"
    assert detail["summary"]["trades"] > 0
    assert get(root, "runs", algorithm="two-up")[1][0]["run_id"] == finished
    stocks = get(root, "runs", finished, "stocks")[1]
    assert [s["profit"] for s in stocks] == sorted((s["profit"] for s in stocks), reverse=True)
    assert get(root, "runs", finished, "years")[1][0]["year"] == 2015
    assert get(root, "runs", finished, "equity")[1]["dates"]
    assert get(root, "runs", finished, "lookahead")[1]["passed"]
    assert get(root, "runs", finished, "code")[1]["code"] == CODE
    assert get(root, "runs", finished, "nothing")[0] == 404
    assert get(root, "runs", "20260101T000000Z_x_00000000")[0] == 404


def test_trades_are_paged_sorted_and_filtered(root, finished):
    total = get(root, "runs", finished, "trades")[1]["total"]
    page = get(root, "runs", finished, "trades", sort="net", order="desc", limit=3)[1]
    assert page["total"] == total and len(page["rows"]) == 3
    nets = [r["net"] for r in page["rows"]]
    assert nets == sorted(nets, reverse=True)
    ticker = page["rows"][0]["ticker"]
    mine = get(root, "runs", finished, "trades", ticker=ticker.lower(), limit=500)[1]
    assert mine["rows"] and {r["ticker"] for r in mine["rows"]} == {ticker}
    taken = get(root, "runs", finished, "trades", book="taken", limit=1)[1]["total"]
    skipped = get(root, "runs", finished, "trades", book="skipped", limit=1)[1]["total"]
    assert taken + skipped == total
    assert get(root, "runs", finished, "trades", sort="1; drop table x")[0] == 400
    assert get(root, "runs", finished, "trades", limit="ten")[0] == 400
    status, text = lab.trades_csv(root, finished)
    assert status == 200 and text.startswith("ticker,") and text.count("\n") == total + 1


def test_one_run_at_a_time(root, fake):
    busy = store.new_run(root, "busy", CODE, {})
    store.set_status(busy, "running", stage="Loading")
    (busy / "pid").write_text(str(os.getpid()))  # a live process
    status, payload = lab.route(
        "POST",
        ["runs"],
        {},
        {"algorithm": "x", "code": CODE},
        root,
        launch=lambda run_dir: pytest.fail("must not start"),
    )
    assert status == 409 and busy.name in payload["error"]


def test_cancel_only_a_running_run(root, finished):
    assert lab.route("POST", ["runs", finished, "cancel"], {}, None, root)[0] == 409


def test_cancel_stops_the_worker(root):
    import subprocess
    import sys

    run_dir = store.new_run(root, "slow", CODE, {})
    child = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(60)"], start_new_session=True
    )
    (run_dir / "pid").write_text(str(child.pid))
    store.set_status(run_dir, "running", stage="Running your algorithm")
    status, found = lab.route("POST", ["runs", run_dir.name, "cancel"], {}, None, root)
    assert status == 200 and found["state"] == "cancelled"
    assert child.wait(timeout=5) is not None


# -- the server's checks ------------------------------------------------------------------
@pytest.fixture
def server(root):
    handler = type(
        "TestHandler",
        (Handler,),
        {"runs_dir": root.parent / "runs", "lab_dir": root, "token": "t0ken", "lab_enabled": True},
    )
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), partial(handler, directory=str(root)))
    handler.port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    yield handler
    httpd.shutdown()
    httpd.server_close()


def call(handler, method, path, body=None, *, host=None, headers=None):
    con = http.client.HTTPConnection("127.0.0.1", handler.port, timeout=10)
    data = json.dumps(body).encode() if isinstance(body, dict) else body
    sent = {"Host": host or f"127.0.0.1:{handler.port}"}
    if data is not None:
        sent["Content-Type"] = "application/json"
    sent.update(headers or {})
    con.request(method, path, body=data, headers=sent)
    response = con.getresponse()
    payload = response.read()
    con.close()
    try:
        return response.status, json.loads(payload)
    except ValueError:
        return response.status, payload.decode()


def test_the_page_gets_the_token_and_can_write(server):
    status, session = call(server, "GET", "/api/lab/session")
    assert status == 200 and session["token"] == "t0ken"
    origin = f"http://localhost:{server.port}"
    status, _ = call(
        server,
        "PUT",
        "/api/lab/algorithms/mine",
        {"code": CODE},
        headers={"X-Kinn-Token": "t0ken", "Origin": origin},
    )
    assert status == 200
    assert call(server, "GET", "/api/lab/algorithms/mine")[1]["code"] == CODE


@pytest.mark.parametrize(
    ("headers", "host"),
    [
        ({}, None),  # no token
        ({"X-Kinn-Token": "wrong"}, None),
        ({"X-Kinn-Token": "t0ken", "Origin": "https://evil.example"}, None),
        ({"X-Kinn-Token": "t0ken"}, "evil.example"),  # DNS rebinding
    ],
)
def test_writes_from_elsewhere_are_refused(server, headers, host):
    status, _ = call(
        server, "PUT", "/api/lab/algorithms/mine", {"code": CODE}, host=host, headers=headers
    )
    assert status == 403
    assert not (server.lab_dir / "algorithms" / "mine.py").exists()


def test_reads_need_this_machines_host(server):
    assert call(server, "GET", "/api/lab/session", host="evil.example")[0] == 403
    assert call(server, "GET", "/api/lab/meta", host=f"localhost:{server.port}")[0] == 200
    assert call(server, "GET", "/api/lab/meta", host="localhost:5173")[0] == 200  # Vite


def test_bodies_must_be_small_json_objects(server):
    token = {"X-Kinn-Token": "t0ken"}
    assert (
        call(
            server,
            "PUT",
            "/api/lab/algorithms/x",
            b"code",
            headers={**token, "Content-Type": "text/plain"},
        )[0]
        == 415
    )
    assert call(server, "PUT", "/api/lab/algorithms/x", b"[1]", headers=token)[0] == 400
    assert call(server, "PUT", "/api/lab/algorithms/x", b"{", headers=token)[0] == 400
    too_long = {**token, "Content-Length": str(1_000_001)}  # refused before it is read
    assert call(server, "PUT", "/api/lab/algorithms/x", b"{}", headers=too_long)[0] == 413


def test_the_lab_is_off_when_the_server_listens_beyond_this_machine(server):
    server.lab_enabled = False
    assert call(server, "GET", "/api/lab/meta")[0] == 403


def test_other_writes_are_not_found(server):
    assert call(server, "POST", "/api/runs", {"x": 1})[0] == 404
