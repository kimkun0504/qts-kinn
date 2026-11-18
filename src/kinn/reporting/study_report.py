"""The event-study report: forward-return curves by minutes held, with confidence intervals."""

from __future__ import annotations

import html
import json
from pathlib import Path

from kinn.reporting.tearsheet import CSS, JS, _table

EXTRA_CSS = ".viz-root{--s3:#1baf7a}@media (prefers-color-scheme:dark){.viz-root{--s3:#199e70}}"


def _p(value, digits=2):
    return "–" if value is None else f"{100 * value:+.{digits}f}%".replace("-", "−")


def _ci(stat):
    if stat["mean"] is None:
        return "–"
    if stat["low"] is None:
        return _p(stat["mean"])
    return f"{_p(stat['mean'])} ({_p(stat['low'])} to {_p(stat['high'])})"


def _label(column: str) -> str:
    return "close" if column == "r_close" else column[2:]


def _curve_chart(curve: dict) -> str:
    columns = list(curve)
    if not columns:
        return "<p>No completed executable horizons. Check unresolved exposure.</p>"
    width, height, left, right, top, bottom = 1000, 300, 56, 110, 12, 34
    series = {k: [curve[c][k]["mean"] for c in columns] for k in ("gross", "net_1x", "net_2x")}
    lows = [curve[c]["net_1x"]["low"] for c in columns]
    highs = [curve[c]["net_1x"]["high"] for c in columns]
    band = all(v is not None for v in lows + highs)
    values = [v for vs in series.values() for v in vs] + (lows + highs if band else []) + [0.0]
    low, high = min(values), max(values)
    span = (high - low) or 1.0
    n = len(columns)

    def x(i):
        return left + (width - left - right) * i / max(n - 1, 1)

    def y(v):
        return top + (height - top - bottom) * (1 - (v - low) / span)

    def path(vals):
        return " ".join(
            f"{'M' if i == 0 else 'L'}{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals)
        )

    out = (
        f"<svg viewBox='0 0 {width} {height}' role='img' aria-label='Mean forward return by "
        "minutes held: gross, net at 1x and net at 2x slippage'>"
    )
    for k in range(5):
        v = low + span * k / 4
        out += (
            f"<line x1='{left}' x2='{width - right}' y1='{y(v):.1f}' y2='{y(v):.1f}' "
            f"stroke='var(--grid)'/><text x='{left - 6}' y='{y(v) + 4:.1f}' "
            f"text-anchor='end'>{100 * v:+.2f}%</text>"
        )
    out += (
        f"<line x1='{left}' x2='{width - right}' y1='{y(0):.1f}' y2='{y(0):.1f}' "
        "stroke='var(--muted)'/>"
    )
    for i, c in enumerate(columns):
        out += f"<text x='{x(i):.1f}' y='{height - 18}' text-anchor='middle'>{_label(c)}</text>"
    out += (
        f"<text x='{(left + width - right) / 2:.0f}' y='{height - 3}' text-anchor='middle'>"
        "minutes held after entry (not to scale; capped at the close)</text>"
    )
    if band:
        pts = [f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(highs)]
        pts += [f"{x(i):.1f},{y(lows[i]):.1f}" for i in range(n - 1, -1, -1)]
        out += f"<polygon points='{' '.join(pts)}' fill='var(--s1)' opacity='0.14'/>"
    out += (
        f"<path d='{path(series['gross'])}' fill='none' stroke='var(--s3)' stroke-width='2' "
        "stroke-dasharray='1 4' stroke-linecap='round'/>"
        f"<path d='{path(series['net_2x'])}' fill='none' stroke='var(--s2)' stroke-width='2' "
        "stroke-dasharray='5 4'/>"
        f"<path d='{path(series['net_1x'])}' fill='none' stroke='var(--s1)' stroke-width='2'/>"
    )
    ends = sorted(
        (
            (series[k][-1], name)
            for k, name in (("gross", "gross"), ("net_1x", "net 1×"), ("net_2x", "net 2×"))
        ),
        reverse=True,
    )
    last_y = -100.0
    for value, name in ends:
        pos = max(y(value), last_y + 13)
        last_y = pos
        out += f"<text x='{width - right + 6}' y='{pos + 4:.1f}'>{name} {100 * value:+.2f}%</text>"
    out += (
        f"<line class='cross' y1='{top}' y2='{height - bottom}' stroke='var(--muted)' "
        "style='display:none'/></svg>"
    )
    points = [
        {
            "x": round(x(i), 1),
            "t": f"<b>held {_label(c)}{'' if c == 'r_close' else ' min'}</b><br>gross "
            f"{_p(curve[c]['gross']['mean'])}<br>net 1× {_ci(curve[c]['net_1x'])}<br>net 2× "
            f"{_p(curve[c]['net_2x']['mean'])}",
        }
        for i, c in enumerate(columns)
    ]
    legend = (
        "<div class='legend'><span class='key' style='border-color:var(--s3);"
        "border-top-style:dotted'></span>gross<span class='key' style='border-color:var(--s1)'>"
        "</span>net, 1× slippage (band: 95% interval)<span class='key' style='border-color:"
        "var(--s2);border-top-style:dashed'></span>net, 2× slippage</div>"
    )
    return (
        f"{legend}<div class='chart' data-points='{html.escape(json.dumps(points))}'>{out}"
        "<div class='tip'></div></div>"
    )


def _split_rows(groups: dict, primary="r_close", secondary="r_60") -> list[list[str]]:
    return [
        [
            label,
            f"{g[primary]['gross']['n']:,}",
            _p(g[primary]["gross"]["mean"]),
            _ci(g[primary]["net_1x"]),
            _p(g[primary]["net_2x"]["mean"]),
            _ci(g[secondary]["net_1x"]),
        ]
        for label, g in groups.items()
    ]


SPLIT_HEAD = [
    "",
    "Events",
    "Gross to close",
    "Net 1× to close (95% interval)",
    "Net 2× to close",
    "Net 1× at 60 min (95% interval)",
]


def render(run_dir: Path) -> tuple[str, str]:
    manifest = json.loads((run_dir / "manifest.json").read_text())
    s = json.loads((run_dir / "study.json").read_text())
    title = f"{manifest['strategy']} · {manifest['config']} · event study"
    head = (
        f"`{manifest['run_id']}` · {manifest['period']['start']} to "
        f"{manifest['period']['end']} · build `{manifest['data_build_id']}` · commit "
        f"`{manifest['git']['commit'][:8]}`"
    )
    if not s["events"]:
        counts = s.get("counts", {})
        facts = (
            f"No filled events. Signals: {counts.get('signals', 0)}; "
            f"unfilled entries: {counts.get('unfilled', 0)}; "
            f"unresolved positions: {counts.get('unresolved_positions', 0)}. "
            "No return, daily P&L t-statistic or drawdown estimate is available."
        )
        return (
            f"<html><body><h1>{html.escape(title)}</h1><p>{html.escape(head)}</p>"
            f"<p>{html.escape(facts)}</p></body></html>",
            f"# {title}\n\n{head}\n\n{facts}\n",
        )
    curve = s["curve"]
    primary = next(iter(curve), "r_close") if s.get("execution_profile") else "r_close"
    secondary = primary if s.get("execution_profile") else "r_60"
    split_head = (
        [
            "",
            "Completed events",
            f"Gross, {_label(primary)} min",
            "Net 1× (95% interval)",
            "Net 2×",
            "Net 1× (95% interval)",
        ]
        if s.get("execution_profile")
        else SPLIT_HEAD
    )
    rows = [
        [
            _label(c) + ("" if c == "r_close" else " min"),
            _ci(curve[c]["gross"]),
            _ci(curve[c]["net_1x"]),
            _ci(curve[c]["net_2x"]),
        ]
        for c in curve
    ]
    curve_head = ["Held", "Gross", "Net, 1× slippage", "Net, 2× slippage"]
    cost = s["mean_cost"]
    facts = (
        f"{s['events']:,} events on {s['sessions_with_events']:,} sessions "
        f"({s['counts']['signals']:,} signals, {s['counts']['unfilled']:,} without an entry). "
        f"Median entry price ${s['median_entry_price']:.2f}, median 20-day dollar volume "
        f"${s['median_adv']:,.0f}. Mean round-trip cost at 1×: {_p(cost['fees'] + cost['slippage_1x'] if cost['fees'] is not None else None).lstrip('+')} "
        f"(fees {_p(cost['fees']).lstrip('+')}, slippage {_p(cost['slippage_1x']).lstrip('+')}). "
        f"{100 * s['capacity_limited_share']:.0f}% of entries are larger than 5% of their bar's "
        f"volume. Lookahead replays passed: {s['counts']['lookahead_checks']:,}."
    )
    if s.get("execution_profile"):
        facts += (
            f" Extended_v1: {s['unresolved_positions']} unresolved positions. "
            "Returns include completed positions only; any unresolved exposure fails the study. "
            "A horizon schedules liquidation; capped orders can fill later. "
            "Both cost cases must fit each limit. Minute bars approximate executable liquidity."
        )
    sections = [
        ("By period", "by_period"),
        ("By liquidity", "by_liquidity"),
        ("By time of the event", "by_time"),
        ("By year", "by_year"),
    ]
    scratch = "<span class='badge'>SCRATCH</span>" if manifest["scratch"] else ""
    page = (
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>"
        f"{html.escape(manifest['run_id'])}</title><style>{CSS}{EXTRA_CSS}</style></head>"
        f"<body class='viz-root'><h1>{html.escape(title)}{scratch}</h1>"
        f"<div class='sub mono'>{html.escape(manifest['run_id'])}</div>"
        f"<p class='sub'>{html.escape(facts)}</p>"
        f"<h2>Mean forward return after the event</h2>{_curve_chart(curve)}"
        f"<h2>Curve (95% intervals resample whole sessions)</h2>{_table(curve_head, rows)}"
        + "".join(
            f"<h2>{name}</h2>{_table(split_head, _split_rows(s[key], primary, secondary))}"
            for name, key in sections
        )
        + f"<script>{JS}</script></body></html>"
    )

    def md_table(headers, body):
        lines = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
        return "\n".join(lines + ["| " + " | ".join(r) + " |" for r in body])

    md = (
        "\n\n".join(
            [
                f"# {title}" + (" (SCRATCH)" if manifest["scratch"] else ""),
                head,
                facts,
                md_table(curve_head, rows),
            ]
            + [
                f"## {name}\n\n" + md_table(split_head, _split_rows(s[key], primary, secondary))
                for name, key in sections
            ]
        )
        + "\n"
    )
    return page, md


def write(run_dir: Path) -> Path:
    page, md = render(run_dir)
    (run_dir / "study.md").write_text(md)
    path = run_dir / "study.html"
    path.write_text(page)
    return path
