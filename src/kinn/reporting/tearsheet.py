"""The standard tearsheet: one self-contained HTML page (and a Markdown summary) per run.

It reads only the run folder (manifest, metrics, equity, trades), like the Workbench.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

CSS = """
.viz-root{color-scheme:light;--surface:#fcfcfb;--panel:#f3f2ee;--ink:#0b0b0b;--ink2:#52514e;
--muted:#8a897f;--grid:#e3e2dc;--s1:#2a78d6;--s2:#eb6834;--bad:#b3261e;
font:14px/1.45 "Inter","IBM Plex Sans",system-ui,sans-serif;background:var(--surface);
color:var(--ink);margin:0;padding:28px 32px;max-width:1080px}
@media (prefers-color-scheme:dark){.viz-root{color-scheme:dark;--surface:#1a1a19;--panel:#242422;
--ink:#f0efec;--ink2:#c3c2b7;--muted:#8f8e85;--grid:#33332f;--s1:#3987e5;--s2:#d95926;--bad:#f2b8b5}}
h1{font-size:20px;margin:0 0 2px}h2{font-size:14px;margin:28px 0 8px;letter-spacing:.02em}
.sub{color:var(--ink2);font-size:13px}.mono{font-family:"JetBrains Mono",ui-monospace,monospace}
.tiles{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:18px 0}
.tile{background:var(--panel);border-radius:8px;padding:10px 12px}
.tile b{display:block;font-size:20px;font-variant-numeric:tabular-nums}
.tile span{color:var(--ink2);font-size:12px}.tile small{color:var(--muted);font-size:12px}
table{border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:13px}
th,td{padding:4px 12px 4px 0;text-align:right;border-bottom:1px solid var(--grid)}
th:first-child,td:first-child{text-align:left}th{color:var(--ink2);font-weight:500}
.badge{display:inline-block;border:1px solid var(--bad);color:var(--bad);border-radius:4px;
padding:0 6px;font-size:12px;margin-left:8px}.cols{display:flex;gap:40px;flex-wrap:wrap}
svg text{fill:var(--ink2);font-size:11px}.tip{position:absolute;pointer-events:none;
background:var(--panel);border:1px solid var(--grid);border-radius:6px;padding:6px 8px;
font-size:12px;display:none;white-space:nowrap}.chart{position:relative}
.legend{font-size:12px;color:var(--ink2);margin:4px 0}.key{display:inline-block;width:18px;
height:0;border-top:2px solid;vertical-align:middle;margin:0 6px 0 14px}
"""

JS = """
for (const box of document.querySelectorAll('.chart[data-points]')) {
  const pts = JSON.parse(box.dataset.points), svg = box.querySelector('svg');
  const tip = box.querySelector('.tip'), line = box.querySelector('.cross');
  svg.addEventListener('mousemove', e => {
    const r = svg.getBoundingClientRect(), W = svg.viewBox.baseVal.width;
    const x = (e.clientX - r.left) / r.width * W;
    let best = pts[0]; for (const p of pts) if (Math.abs(p.x - x) < Math.abs(best.x - x)) best = p;
    line.setAttribute('x1', best.x); line.setAttribute('x2', best.x); line.style.display = '';
    tip.innerHTML = best.t; tip.style.display = 'block';
    tip.style.left = Math.min(e.clientX - r.left + 12, r.width - 190) + 'px'; tip.style.top = '8px';
  });
  svg.addEventListener('mouseleave', () => { tip.style.display = 'none'; line.style.display = 'none'; });
}
"""


def _pct(value, digits=2):
    return "–" if value is None else f"{100 * value:+.{digits}f}%".replace("-", "−")


def _money(value):
    return "–" if value is None else f"{value:+,.0f}".replace("+", "+$").replace("-", "−$")


def _num(value, digits=2):
    return "–" if value is None else f"{value:,.{digits}f}".replace("-", "−")


def _table(head: list[str], rows: list[list[str]]) -> str:
    out = "<table><tr>" + "".join(f"<th>{html.escape(h)}</th>" for h in head) + "</tr>"
    for row in rows:
        out += "<tr>" + "".join(f"<td>{html.escape(str(c))}</td>" for c in row) + "</tr>"
    return out + "</table>"


def _equity_chart(dates: list, one: list[float], two: list[float]) -> str:
    width, height, left, right, top, bottom = 1000, 280, 56, 120, 12, 24
    n = len(dates)
    if n < 2:
        return "<p class='sub'>Not enough sessions for a chart.</p>"
    step = max(1, n // 600)
    idx = list(range(0, n, step))
    if idx[-1] != n - 1:
        idx.append(n - 1)
    low, high = min(min(one), min(two), 0.0), max(max(one), max(two), 0.0)
    span = (high - low) or 1.0

    def x(i):
        return left + (width - left - right) * i / (n - 1)

    def y(v):
        return top + (height - top - bottom) * (1 - (v - low) / span)

    def path(values):
        return " ".join(
            f"{'M' if k == 0 else 'L'}{x(i):.1f},{y(values[i]):.1f}" for k, i in enumerate(idx)
        )

    grid = ""
    for k in range(5):
        value = low + span * k / 4
        grid += (
            f"<line x1='{left}' x2='{width - right}' y1='{y(value):.1f}' y2='{y(value):.1f}' "
            f"stroke='var(--grid)'/><text x='{left - 6}' y='{y(value) + 4:.1f}' "
            f"text-anchor='end'>{value:,.0f}</text>"
        )
    years = ""
    year_count = len({str(d)[:4] for d in dates})
    every = 1 if year_count <= 12 else 2
    seen: list[str] = []
    for i in range(n):
        year = str(dates[i])[:4]
        if year not in seen:
            seen.append(year)
            if (len(seen) - 1) % every == 0:
                years += f"<text x='{x(i):.1f}' y='{height - 6}'>{year}</text>"
    points = [
        {
            "x": round(x(i), 1),
            "t": f"<b>{dates[i]}</b><br>1× slippage: {one[i]:,.0f}<br>2× slippage: {two[i]:,.0f}",
        }
        for i in idx
    ]
    end1, end2 = y(one[-1]), y(two[-1])
    if abs(end1 - end2) < 14:
        end2 = end1 + (14 if two[-1] <= one[-1] else -14)
    return (
        "<div class='legend'><span class='key' style='border-color:var(--s1)'></span>1× slippage"
        "<span class='key' style='border-color:var(--s2);border-top-style:dashed'></span>"
        "2× slippage</div>"
        f"<div class='chart' data-points='{html.escape(json.dumps(points))}'>"
        f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='Cumulative net profit in "
        f"dollars at 1x and 2x slippage'>{grid}{years}"
        f"<line x1='{left}' x2='{width - right}' y1='{y(0):.1f}' y2='{y(0):.1f}' "
        "stroke='var(--muted)'/>"
        f"<path d='{path(two)}' fill='none' stroke='var(--s2)' stroke-width='2' "
        "stroke-dasharray='5 4'/>"
        f"<path d='{path(one)}' fill='none' stroke='var(--s1)' stroke-width='2'/>"
        f"<text x='{width - right + 6}' y='{end1 + 4:.1f}'>1× {one[-1]:,.0f}</text>"
        f"<text x='{width - right + 6}' y='{end2 + 4:.1f}'>2× {two[-1]:,.0f}</text>"
        f"<line class='cross' y1='{top}' y2='{height - bottom}' stroke='var(--muted)' "
        "style='display:none'/></svg><div class='tip'></div></div>"
    )


def _histogram(returns: np.ndarray) -> str:
    if len(returns) < 5:
        return "<p class='sub'>Too few trades for a distribution.</p>"
    lo, hi = np.percentile(returns, [1, 99])
    if hi <= lo:
        return ""
    counts, edges = np.histogram(np.clip(returns, lo, hi), bins=40, range=(lo, hi))
    width, height, left, bottom = 480, 160, 8, 22
    bar = (width - 2 * left) / len(counts)
    peak = counts.max() or 1
    out = f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='Distribution of net "
    out += "return per trade' style='max-width:480px'>"
    for k, count in enumerate(counts):
        h = (height - bottom - 6) * count / peak
        out += (
            f"<rect x='{left + k * bar + 1:.1f}' y='{height - bottom - h:.1f}' "
            f"width='{bar - 2:.1f}' height='{h:.1f}' rx='2' fill='var(--s1)'>"
            f"<title>{100 * edges[k]:+.2f}% to {100 * edges[k + 1]:+.2f}%: {count} trades"
            "</title></rect>"
        )
    zero = left + (0 - lo) / (hi - lo) * (width - 2 * left)
    if left < zero < width - left:
        out += (
            f"<line x1='{zero:.1f}' x2='{zero:.1f}' y1='0' y2='{height - bottom}' "
            "stroke='var(--muted)'/>"
        )
    out += (
        f"<text x='{left}' y='{height - 6}'>{100 * lo:+.1f}%</text>"
        f"<text x='{width - left}' y='{height - 6}' text-anchor='end'>{100 * hi:+.1f}%</text>"
        f"<text x='{zero:.1f}' y='{height - 6}' text-anchor='middle'>0</text></svg>"
    )
    return (
        out
        + "<p class='sub'>Net return per trade at 1× slippage, clipped at the 1st and 99th percentiles.</p>"
    )


def render(run_dir: Path) -> tuple[str, str]:
    """(HTML, Markdown) for a finished run."""
    manifest = json.loads((run_dir / "manifest.json").read_text())
    m = json.loads((run_dir / "metrics.json").read_text())
    equity = pq.read_table(run_dir / "equity.parquet").to_pydict()
    trades = pq.read_table(run_dir / "trades.parquet", columns=["net", "notional"]).to_pydict()
    returns = (
        np.array(trades["net"]) / np.array(trades["notional"]) if trades["net"] else np.array([])
    )
    one, two = m["slippage_1x"], m["slippage_2x"]
    counts = m["counts"]
    scratch = (
        "<span class='badge'>SCRATCH – excluded from reports</span>" if manifest["scratch"] else ""
    )
    tiles = [
        ("Net return per trade", _pct(one["mean_return"]), f"2×: {_pct(two['mean_return'])}"),
        ("Trades", f"{m['trades']:,}", f"{_num(m['trades_per_session'])} a session"),
        (
            "Win rate",
            _pct(one["win_rate"], 1).lstrip("+"),
            f"2×: {_pct(two['win_rate'], 1).lstrip('+')}",
        ),
        ("Median return", _pct(one["median_return"]), f"gross mean {_pct(m['gross_mean_return'])}"),
        ("Total net", _money(one["total_net"]), f"2×: {_money(two['total_net'])}"),
        ("Sharpe (daily)", _num(one["sharpe"]), f"2×: {_num(two['sharpe'])}"),
        ("t-stat (daily P&L)", _num(one["t_stat_daily"]), f"2×: {_num(two['t_stat_daily'])}"),
        ("Max drawdown", _money(one["max_drawdown"]), f"on ${m['equity']:,.0f} equity"),
    ]
    tile_html = "".join(
        f"<div class='tile'><span>{html.escape(a)}</span><b>{html.escape(b)}</b>"
        f"<small>{html.escape(c)}</small></div>"
        for a, b, c in tiles
    )
    years = [
        [
            y,
            f"{r['trades']:,}",
            _pct(r["mean_return_1x"]),
            _pct(r["mean_return_2x"]),
            _money(r["net_1x"]),
        ]
        for y, r in m["by_year"].items()
    ]
    costs = m["cost_bps_of_notional"]
    cost_rows = [[k.replace("_", " "), _num(v, 1)] for k, v in costs.items()]
    funnel = [
        ["signals", f"{counts['signals']:,}"],
        ["rejected: capital or duplicate", f"{counts['rejected_capital']:,}"],
        ["rejected: position too small", f"{counts['rejected_size']:,}"],
        ["entry never filled", f"{counts['unfilled']:,}"],
        ["trades", f"{m['trades']:,}"],
        ["lookahead replays passed", f"{counts['lookahead_checks']:,}"],
    ]
    exits = [[k, f"{v:,}"] for k, v in sorted(m["exit_reasons"].items(), key=lambda kv: -kv[1])]
    git = manifest["git"]
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>{html.escape(manifest["run_id"])}</title><style>{CSS}</style></head><body class="viz-root">
<h1>{html.escape(manifest["strategy"])} · {html.escape(manifest["config"])}{scratch}</h1>
<div class="sub mono">{html.escape(manifest["run_id"])}</div>
<div class="sub">{manifest["period"]["start"]} to {manifest["period"]["end"]} · {m["sessions"]:,} sessions ·
agent {html.escape(manifest["agent"])} · commit <span class="mono">{git["commit"][:8]}</span>
{"(uncommitted changes)" if git["dirty"] else ""} · data build <span class="mono">{manifest["data_build_id"]}</span>
· costs {html.escape(manifest["cost_calibration"])}</div>
<div class="tiles">{tile_html}</div>
<h2>Cumulative net profit, dollars</h2>{_equity_chart(equity["date"], equity["cum_net"], equity["cum_net_2x"])}
<h2>By year</h2>{_table(["Year", "Trades", "Net / trade, 1×", "Net / trade, 2×", "Net $, 1×"], years)}
<div class="cols"><div><h2>Round-trip costs, bps of entry notional</h2>{_table(["Cost", "bps"], cost_rows)}</div>
<div><h2>From signal to trade</h2>{_table(["Stage", "Count"], funnel)}</div>
<div><h2>Exits</h2>{_table(["Reason", "Trades"], exits)}</div></div>
<h2>Distribution</h2>{_histogram(returns)}
<script>{JS}</script></body></html>"""
    md = "\n".join(
        [
            f"# {manifest['strategy']} · {manifest['config']}"
            + (" (SCRATCH)" if manifest["scratch"] else ""),
            f"`{manifest['run_id']}` · {manifest['period']['start']} to {manifest['period']['end']} · "
            f"build `{manifest['data_build_id']}` · commit `{git['commit'][:8]}`",
            "",
            "| | 1× slippage | 2× slippage |",
            "|---|---|---|",
            f"| Net return per trade | {_pct(one['mean_return'])} | {_pct(two['mean_return'])} |",
            f"| Win rate | {_pct(one['win_rate'], 1).lstrip('+')} | {_pct(two['win_rate'], 1).lstrip('+')} |",
            f"| Total net | {_money(one['total_net'])} | {_money(two['total_net'])} |",
            f"| Sharpe (daily) | {_num(one['sharpe'])} | {_num(two['sharpe'])} |",
            f"| t-stat (daily P&L) | {_num(one['t_stat_daily'])} | {_num(two['t_stat_daily'])} |",
            "",
            f"Trades: {m['trades']:,} over {m['sessions']:,} sessions. Gross mean return per trade: "
            f"{_pct(m['gross_mean_return'])}. Signals {counts['signals']:,}, unfilled "
            f"{counts['unfilled']:,}, rejected {counts['rejected_capital'] + counts['rejected_size']:,}.",
            "",
        ]
    )
    return page, md


def write(run_dir: Path) -> Path:
    page, md = render(run_dir)
    (run_dir / "tearsheet.md").write_text(md)
    path = run_dir / "tearsheet.html"
    path.write_text(page)
    return path
