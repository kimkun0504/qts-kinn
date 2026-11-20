"""The Lab's endpoints and the server's checks on them (decision 0023)."""

from __future__ import annotations

import gzip
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


def _busy(root):
    busy = store.new_run(root, "busy", CODE, {})
    store.set_status(busy, "running", stage="Loading")
    (busy / "pid").write_text(str(os.getpid()))
    return busy


def _never(run_dir):
    pytest.fail(f"must not start {run_dir.name}")


def _post(root, launch=_never, name="x"):
    return lab.route("POST", ["runs"], {}, {"algorithm": name, "code": CODE}, root, launch=launch)


def test_a_run_started_while_another_goes_waits_its_turn(root):
    busy = _busy(root)
    started = []
    status, payload = _post(root, started.append)
    assert status == 202 and not started
    assert payload["status"]["state"] == "waiting" and payload["status"]["ahead"] == 1
    second = _post(root, started.append, "y")[1]
    assert second["status"]["ahead"] == 2
    assert get(root, "runs", second["run_id"], "status")[1]["ahead"] == 2

    store.set_status(busy, "complete")
    first = store.dispatch(root, started.append)
    assert first is not None and first.name == payload["run_id"] and started == [first]
    assert store.status(first)["state"] == "queued"
    assert store.dispatch(root, started.append) is None
    assert get(root, "runs", second["run_id"], "status")[1]["ahead"] == 1


def test_the_same_run_is_not_queued_twice(root):
    busy = _busy(root)
    first = _post(root)
    assert first[0] == 202
    status, payload = _post(root)
    assert status == 409 and first[1]["run_id"] in payload["error"]
    changed = {"algorithm": "x", "code": CODE + "\n"}
    assert lab.route("POST", ["runs"], {}, changed, root, launch=_never)[0] == 202
    status, payload = _post(root, name="busy")
    assert status == 409 and busy.name in payload["error"]


def test_a_run_another_workbench_claimed_is_not_started_again(root):
    busy = _busy(root)
    waiting = _post(root)[1]["run_id"]
    store.set_status(busy, "complete")
    (store.run_dir_of(root, waiting) / "claimed").touch()
    assert store.dispatch(root, _never) is None


def test_a_waiting_run_can_be_cancelled_and_is_skipped(root):
    busy = _busy(root)
    waiting = _post(root)[1]["run_id"]
    assert lab.route("POST", ["runs", waiting, "cancel"], {}, None, root)[1]["state"] == "cancelled"
    store.set_status(busy, "complete")
    assert store.dispatch(root, _never) is None


def test_the_queue_has_a_limit(root, monkeypatch):
    _busy(root)
    monkeypatch.setattr(store, "MAX_WAITING", 2)
    assert _post(root, name="a")[0] == 202
    assert _post(root, name="b")[0] == 202
    status, payload = _post(root, name="c")
    assert status == 409 and "waiting already" in payload["error"]


def test_the_queue_moves_on_by_itself(root):
    busy = _busy(root)
    waiting = _post(root)[1]["run_id"]
    store.set_status(busy, "complete")
    stop = threading.Event()
    started = []

    def launch(run_dir):
        started.append(run_dir.name)
        stop.set()

    worker = threading.Thread(target=lab.keep_dispatching, args=(root, launch, 0.01, stop))
    worker.start()
    worker.join(5)
    assert started == [waiting]


def test_a_worker_that_cannot_start_fails_the_run_and_frees_the_lab(root):
    def broken(run_dir):
        raise OSError("no such file")

    status, payload = lab.route(
        "POST", ["runs"], {}, {"algorithm": "x", "code": CODE}, root, launch=broken
    )
    assert status == 500 and "could not start" in payload["error"]
    assert store.active_run(root) is None
    assert store.read_algorithm(root, "x") == CODE


def test_a_queued_run_whose_worker_never_started_is_let_go(root):
    run_dir = store.new_run(root, "x", CODE, {})
    old = os.stat(run_dir / "status.json").st_mtime - 3600
    os.utime(run_dir / "status.json", (old, old))
    assert store.status(run_dir)["state"] == "interrupted"
    assert store.active_run(root) is None


def test_cancel_only_a_running_run(root, finished):
    assert lab.route("POST", ["runs", finished, "cancel"], {}, None, root)[0] == 409


def test_a_note_on_a_run_is_kept_listed_and_cleared(root, finished):
    def put(note):
        return lab.route("PUT", ["runs", finished, "note"], {}, {"note": note}, root)

    assert put("  Tried a 20-day hold after the sweep.  ") == (
        200,
        {"run_id": finished, "note": "Tried a 20-day hold after the sweep."},
    )
    assert get(root, "runs", finished)[1]["note"] == "Tried a 20-day hold after the sweep."
    assert get(root, "runs")[1][0]["note"] == "Tried a 20-day hold after the sweep."
    assert put("x" * 2_001)[0] == 400 and put(5)[0] == 400
    assert put("")[1]["note"] == "" and get(root, "runs", finished)[1]["note"] == ""
    assert not (root / "runs" / finished / "note.txt").exists()
    assert lab.route("PUT", ["runs", "nope", "note"], {}, {"note": "x"}, root)[0] == 404


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


def test_the_code_check_endpoint_reads_without_running(root):
    status, payload = lab.route(
        "POST", ["check"], {}, {"code": "import os\nos.remove('x')\n"}, root
    )
    assert status == 200
    assert [f["severity"] for f in payload["findings"]] == ["error"]  # no signal; nothing ran
    status, payload = lab.route("POST", ["check"], {}, {"code": "x = 1\n", "module": True}, root)
    assert (status, payload) == (200, {"findings": []})
    assert lab.route("POST", ["check"], {}, {"code": 3}, root)[0] == 400


def test_a_run_of_broken_code_is_refused_and_makes_no_run(root):
    status, payload = lab.route(
        "POST", ["runs"], {}, {"algorithm": "x", "code": "def signal(data)\n"}, root,
        launch=lambda run_dir: pytest.fail("must not start"),
    )  # fmt: skip
    assert status == 400 and payload["error"].startswith("Line 1: Syntax error")
    assert lab.route("GET", ["runs"], {}, None, root)[1] == []


def test_the_library_endpoints(root):
    code = '"""Shared helpers."""\n\ndef f(x):\n    return x\n'
    assert lab.route("PUT", ["library", "helpers"], {}, {"code": code}, root)[0] == 200
    assert lab.route("PUT", ["library", "Bad-Name"], {}, {"code": code}, root)[0] == 400
    status, rows = lab.route("GET", ["library"], {}, None, root)
    assert status == 200 and rows[0]["name"] == "helpers" and rows[0]["description"]
    assert lab.route("GET", ["library", "helpers"], {}, None, root)[1]["code"] == code
    assert lab.route("DELETE", ["library", "helpers"], {}, None, root)[0] == 200
    assert lab.route("GET", ["library", "helpers"], {}, None, root)[0] == 404
    assert any(p.name.startswith("library-helpers-") for p in (root / "trash").iterdir())


def test_the_history_endpoints(root):
    lab.route("PUT", ["algorithms", "h"], {}, {"code": "first\n"}, root)
    lab.route("PUT", ["algorithms", "h"], {}, {"code": "second\n"}, root)
    status, versions = lab.route("GET", ["algorithms", "h", "history"], {}, None, root)
    assert status == 200 and versions[0]["first_line"] == "first"
    found = lab.route("GET", ["algorithms", "h", "history", versions[0]["version"]], {}, None, root)
    assert found == (200, {"version": versions[0]["version"], "code": "first\n"})
    assert lab.route("GET", ["algorithms", "h", "history", "nope"], {}, None, root)[0] == 404
    lab.route("PUT", ["library", "m"], {}, {"code": "x = 1\n"}, root)
    lab.route("PUT", ["library", "m"], {}, {"code": "x = 2\n"}, root)
    assert (
        lab.route("GET", ["library", "m", "history"], {}, None, root)[1][0]["first_line"] == "x = 1"
    )


def test_a_bad_sweep_is_refused_and_a_good_one_is_kept_with_the_run(root):
    bad = {"field": "universe.min_price", "values": [1, 2]}
    status, payload = lab.route(
        "POST", ["runs"], {}, {"algorithm": "x", "code": CODE, "sweep": bad}, root,
        launch=lambda run_dir: pytest.fail("must not start"),
    )  # fmt: skip
    assert status == 400 and "sweep" in payload["error"]
    started = []
    good = {"field": "exit.hold_days", "values": [5, 10]}
    status, payload = lab.route(
        "POST", ["runs"], {}, {"algorithm": "x", "code": CODE, "sweep": good}, root,
        launch=started.append,
    )  # fmt: skip
    assert status == 202 and started
    request = json.loads((started[0] / "request.json").read_text())
    assert request["sweep"] == good
    assert "exit.hold_days" in get(root, "meta")[1]["sweepable"]


def test_a_large_answer_is_gzipped_only_for_a_client_that_asks(server):
    big = CODE + "\n#" + "x" * 40_000 + "\n"
    origin = f"http://localhost:{server.port}"
    headers = {"X-Kinn-Token": "t0ken", "Origin": origin}
    assert call(server, "PUT", "/api/lab/algorithms/big", {"code": big}, headers=headers)[0] == 200
    answers = {}
    for encoding in ("gzip", "identity"):
        con = http.client.HTTPConnection("127.0.0.1", server.port, timeout=10)
        con.request("GET", "/api/lab/algorithms/big", headers={"Accept-Encoding": encoding})
        response = con.getresponse()
        answers[encoding] = (response.getheader("Content-Encoding"), response.read())
        con.close()
    assert answers["gzip"][0] == "gzip" and answers["identity"][0] is None
    assert gzip.decompress(answers["gzip"][1]) == answers["identity"][1]
    assert json.loads(answers["identity"][1])["code"] == big


def test_the_guides_are_served_read_only(server):
    status, guide = call(server, "GET", "/api/guide/lab")
    assert status == 200 and guide["name"] == "LAB.md" and guide["text"].startswith("# ")
    assert call(server, "GET", "/api/guide/workbench")[1]["name"] == "README.md"
    assert call(server, "GET", "/api/guide/secrets")[0] == 404
    assert call(server, "GET", "/api/guide/..%2F..%2F.env")[0] == 404
