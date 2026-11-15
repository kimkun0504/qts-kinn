// Kinn workbench. Reads /api/* (the run store) and nothing else.
const S = { runs: [], families: [], family: null, run: null, compare: [], tab: "run", detail: {} };
const COLORS = ["var(--s1)", "var(--s2)", "var(--s3)", "var(--s4)"];
const $ = (id) => document.getElementById(id);
const esc = (v) => String(v ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pct = (v, d = 2) => v == null ? "–" : ((v >= 0 ? "+" : "−") + Math.abs(100 * v).toFixed(d) + "%");
const num = (v, d = 2) => v == null ? "–" : (v < 0 ? "−" : "") + Math.abs(v).toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });
const money = (v) => v == null ? "–" : (v < 0 ? "−$" : "+$") + Math.abs(Math.round(v)).toLocaleString("en-US");
const cls = (v) => (v != null && v < 0 ? "neg" : "");
const get = (url) => fetch(url).then((r) => r.ok ? r.json() : null);

function visibleRuns() { return S.runs.filter((r) => !S.family || r.family === S.family); }

async function load() {
  [S.runs, S.families] = await Promise.all([get("/api/runs"), get("/api/families")]);
  const info = await get("/api/info");
  $("store").textContent = `${S.runs.length} runs in ${info.runs_dir}`;
  if (!S.run && S.runs.length) S.run = S.runs[0].run_id;
  draw();
}

function draw() { drawFamilies(); drawRuns(); drawPanel(); }

function drawFamilies() {
  const all = `<button class="fam" type="button" data-family="" aria-pressed="${!S.family}"><b>All families</b><small>${S.runs.length} runs</small></button>`;
  $("families").innerHTML = "<h2>Trials charged, by family</h2>" + all + S.families.map((f) =>
    `<button class="fam" type="button" data-family="${esc(f.family)}" aria-pressed="${S.family === f.family}">
     <b>${esc(f.family)}</b><span class="count">${f.trials}</span>
     <small> trials: ${f.counted} run${f.counted === 1 ? "" : "s"} here${f.prior_trials ? ` + ${f.prior_trials} earlier` : ""}${f.scratch ? `, ${f.scratch} scratch not counted` : ""}</small></button>`).join("");
  for (const b of $("families").querySelectorAll(".fam")) b.onclick = () => { S.family = b.dataset.family || null; draw(); };
}

function drawRuns() {
  const rows = visibleRuns();
  if (!rows.length) { $("runs").innerHTML = `<p class="empty">No runs yet. Start one with <span class="mono">uv run kinn run &lt;strategy&gt; --config &lt;name&gt;</span>, then reload.</p>`; return; }
  $("runs").innerHTML = `<div class="tablewrap"><table><thead><tr><th class="l">Compare</th><th class="l">Started (UTC)</th><th class="l">Strategy</th><th class="l">Config</th><th class="l">Kind</th><th class="l">Agent</th><th>Trades</th><th>Gross / trade</th><th>Net 1×</th><th>Net 2×</th><th>Sharpe</th><th class="l">Notes</th></tr></thead><tbody>` +
    rows.map((r) => {
      const notes = [r.scratch ? "scratch" : "", r.dirty ? "uncommitted code" : "", r.status !== "complete" ? r.status : "", r.schema_ok ? "" : "unknown schema"].filter(Boolean).join(", ");
      const can = r.kind === "backtest" && r.status === "complete";
      return `<tr tabindex="0" data-run="${esc(r.run_id)}" aria-selected="${S.run === r.run_id}">
        <td class="l">${can ? `<input type="checkbox" aria-label="Compare ${esc(r.config)}" data-cmp="${esc(r.run_id)}" ${S.compare.includes(r.run_id) ? "checked" : ""}>` : ""}</td>
        <td class="l mono">${esc(r.started_at.slice(0, 16).replace("T", " "))}</td><td class="l">${esc(r.strategy)}</td><td class="l">${esc(r.config)}</td>
        <td class="l">${r.kind === "event_study" ? "event study" : "backtest"}</td><td class="l">${esc(r.agent)}</td>
        <td>${r.trades == null ? "–" : r.trades.toLocaleString("en-US")}</td><td class="${cls(r.gross)}">${pct(r.gross)}</td>
        <td class="${cls(r.net_1x)}">${pct(r.net_1x)}</td><td class="${cls(r.net_2x)}">${pct(r.net_2x)}</td>
        <td class="${cls(r.sharpe)}">${num(r.sharpe)}</td><td class="l flag">${esc(notes)}</td></tr>`;
    }).join("") + "</tbody></table></div>";
  for (const tr of $("runs").querySelectorAll("tbody tr")) {
    const pick = () => { S.run = tr.dataset.run; S.tab = "run"; draw(); };
    tr.onclick = (e) => { if (e.target.tagName !== "INPUT") pick(); };
    tr.onkeydown = (e) => { if (e.key === "Enter") pick(); };
  }
  for (const box of $("runs").querySelectorAll("input[data-cmp]")) box.onchange = () => {
    const id = box.dataset.cmp;
    if (box.checked) { if (S.compare.length >= 4) { box.checked = false; return; } S.compare.push(id); }
    else S.compare = S.compare.filter((x) => x !== id);
    S.tab = "compare"; drawPanel();
  };
}

// ---- charts -------------------------------------------------------------------------
function lineChart({ labels, series, band, fmt, tipTitle, height = 250, everyLabel = false, zero = true }) {
  const W = 1000, L = 62, R = 128, T = 10, B = 26, n = labels.length;
  const all = series.flatMap((s) => s.values).concat(band ? band.low.concat(band.high) : [], zero ? [0] : []).filter((v) => v != null);
  const lo = Math.min(...all), hi = Math.max(...all), span = hi - lo || 1;
  const x = (i) => L + (W - L - R) * (n === 1 ? 0.5 : i / (n - 1)), y = (v) => T + (height - T - B) * (1 - (v - lo) / span);
  let g = "";
  for (let k = 0; k < 5; k++) { const v = lo + span * k / 4; g += `<line x1="${L}" x2="${W - R}" y1="${y(v)}" y2="${y(v)}" stroke="var(--line)"/><text x="${L - 6}" y="${y(v) + 4}" text-anchor="end">${fmt(v)}</text>`; }
  if (zero) g += `<line x1="${L}" x2="${W - R}" y1="${y(0)}" y2="${y(0)}" stroke="var(--muted)"/>`;
  const stepL = everyLabel ? 1 : Math.ceil(n / 9);
  let last = null;
  labels.forEach((lab, i) => {
    const show = everyLabel ? lab : lab.slice(0, 4);
    if (everyLabel || (show !== last && (i === 0 || i % stepL === 0 || labels[i - 1].slice(0, 4) !== show))) {
      if (everyLabel || show !== last) g += `<text x="${x(i)}" y="${height - 8}" text-anchor="middle">${esc(show)}</text>`;
      last = show;
    }
  });
  if (band) g += `<polygon points="${band.high.map((v, i) => `${x(i)},${y(v)}`).concat(band.low.map((v, i) => `${x(i)},${y(v)}`).reverse()).join(" ")}" fill="${band.color}" opacity="0.16"/>`;
  const ends = [];
  series.forEach((s) => {
    const d = s.values.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join(" ");
    g += `<path d="${d}" fill="none" stroke="${s.color}" stroke-width="2" ${s.dash ? `stroke-dasharray="${s.dash}"` : ""}/>`;
    ends.push({ y: y(s.values[n - 1]), text: `${s.short || s.name} ${fmt(s.values[n - 1])}` });
  });
  ends.sort((a, b) => a.y - b.y);
  let prev = -99;
  for (const e of ends) { const yy = Math.max(e.y, prev + 13); prev = yy; g += `<text x="${W - R + 6}" y="${yy + 4}">${esc(e.text)}</text>`; }
  g += `<line class="cross" y1="${T}" y2="${height - B}" stroke="var(--muted)" style="display:none"/>`;
  const legend = series.length > 1 ? `<p class="legend">${series.map((s) => `<span class="key" style="border-color:${s.color};${s.dash ? "border-top-style:dashed" : ""}"></span>${esc(s.name)}`).join("")}</p>` : "";
  const box = document.createElement("div");
  box.innerHTML = `${legend}<div class="chart"><svg viewBox="0 0 ${W} ${height}" role="img" aria-label="${esc(tipTitle)}">${g}</svg><div class="tip"></div></div>`;
  const svg = box.querySelector("svg"), tip = box.querySelector(".tip"), cross = box.querySelector(".cross");
  svg.onmousemove = (e) => {
    const r = svg.getBoundingClientRect(), px = (e.clientX - r.left) / r.width * W;
    const i = Math.max(0, Math.min(n - 1, Math.round((px - L) / (W - L - R) * (n - 1))));
    cross.setAttribute("x1", x(i)); cross.setAttribute("x2", x(i)); cross.style.display = "";
    tip.innerHTML = `<b>${esc(labels[i])}</b>` + series.map((s) => `<br>${esc(s.name)}: ${fmt(s.values[i])}`).join("") + (band ? `<br>95% interval: ${fmt(band.low[i])} to ${fmt(band.high[i])}` : "");
    tip.style.display = "block"; tip.style.left = Math.min(e.clientX - r.left + 14, r.width - 230) + "px";
  };
  svg.onmouseleave = () => { tip.style.display = "none"; cross.style.display = "none"; };
  return box;
}

function histogram(h) {
  const W = 480, H = 150, L = 6, B = 20, n = h.counts.length, peak = Math.max(...h.counts), bw = (W - 2 * L) / n;
  const lo = h.edges[0], hi = h.edges[n];
  let g = h.counts.map((c, k) => { const hh = (H - B - 6) * c / peak; return `<rect x="${L + k * bw + 1}" y="${H - B - hh}" width="${bw - 2}" height="${hh}" rx="2" fill="var(--s1)"><title>${pct(h.edges[k])} to ${pct(h.edges[k + 1])}: ${c} trades</title></rect>`; }).join("");
  const z = L + (0 - lo) / (hi - lo) * (W - 2 * L);
  if (z > L && z < W - L) g += `<line x1="${z}" x2="${z}" y1="0" y2="${H - B}" stroke="var(--muted)"/><text x="${z}" y="${H - 5}" text-anchor="middle">0</text>`;
  g += `<text x="${L}" y="${H - 5}">${pct(lo, 1)}</text><text x="${W - L}" y="${H - 5}" text-anchor="end">${pct(hi, 1)}</text>`;
  return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Distribution of net return per trade">${g}</svg>`;
}

const table = (head, rows) => `<table><thead><tr>${head.map((h, i) => `<th class="${i ? "" : "l"}">${esc(h)}</th>`).join("")}</tr></thead><tbody>${rows.map((r) => `<tr style="cursor:default">${r.map((c, i) => `<td class="${i ? "" : "l"} ${typeof c === "string" && c.startsWith("−") ? "neg" : ""}">${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
const fact = (label, value, small = "") => `<div><span>${esc(label)}</span><b class="${String(value).startsWith("−") ? "neg" : ""}">${value}</b>${small ? `<small>${small}</small>` : ""}</div>`;

async function detail(id) { return S.detail[id] ??= await get(`/api/runs/${encodeURIComponent(id)}`); }

// ---- panels -------------------------------------------------------------------------
async function drawPanel() {
  for (const b of document.querySelectorAll(".tabs button")) { b.setAttribute("aria-selected", b.dataset.tab === S.tab); b.onclick = () => { S.tab = b.dataset.tab; drawPanel(); }; }
  const el = $("panel");
  if (S.tab === "run") return panelRun(el);
  if (S.tab === "compare") return panelCompare(el);
  if (S.tab === "heatmap") return panelHeatmap(el);
  return panelTrials(el);
}

function header(m) {
  const flags = [m.scratch ? "scratch, not counted" : "counted trial", m.git.dirty ? "uncommitted code" : ""].filter(Boolean).join("; ");
  return `<h2>${esc(m.strategy)}, config ${esc(m.config)} <span class="flag">${esc(flags)}</span></h2>
  <p class="note mono">${esc(m.run_id)}</p>
  <p class="note">${esc(m.period.start)} to ${esc(m.period.end)}. Agent ${esc(m.agent)} on ${esc(m.git.branch)} at <span class="mono">${esc(m.git.commit.slice(0, 8))}</span>. Data build <span class="mono">${esc(m.data_build_id)}</span>, costs ${esc(m.cost_calibration)}.</p>`;
}

async function panelRun(el) {
  if (!S.run) { el.innerHTML = `<p class="empty">Pick a run in the table.</p>`; return; }
  const d = await detail(S.run);
  if (!d) { el.innerHTML = `<p class="empty">That run folder could not be read.</p>`; return; }
  if (d.manifest.kind === "event_study") return panelStudy(el, d);
  const m = d.metrics;
  if (!m) { el.innerHTML = header(d.manifest) + `<p class="empty">This run has not finished. Continue it with <span class="mono">uv run kinn run --resume ${esc(d.manifest.run_id)}</span>.</p>`; return; }
  const a = m.slippage_1x, b = m.slippage_2x, c = m.counts;
  el.innerHTML = header(d.manifest) + `<div class="facts">
    ${fact("Net return per trade", pct(a.mean_return), "2× " + pct(b.mean_return))}${fact("Gross per trade", pct(m.gross_mean_return))}
    ${fact("Trades", m.trades.toLocaleString("en-US"), num(m.trades_per_session, 1) + " a session")}${fact("Win rate", pct(a.win_rate, 1).slice(1), "2× " + pct(b.win_rate, 1).slice(1))}
    ${fact("Total net", money(a.total_net), "2× " + money(b.total_net))}${fact("Sharpe, daily", num(a.sharpe), "2× " + num(b.sharpe))}
    ${fact("t-stat, daily P&L", num(a.t_stat_daily))}${fact("Max drawdown", money(a.max_drawdown), "on $" + m.equity.toLocaleString("en-US"))}</div>
    <div class="grid2"><div class="card"><h2>Cumulative net profit, dollars</h2><div id="eq"></div></div>
    <div class="card"><h2>Net return per trade, 1× slippage</h2>${d.histogram ? histogram(d.histogram) : `<p class="dim">Too few trades.</p>`}<p class="dim">Clipped at the 1st and 99th percentiles.</p></div></div>
    <div class="grid2" style="margin-top:18px"><div class="card"><h2>By year</h2>${table(["Year", "Trades", "Net / trade 1×", "Net / trade 2×", "Net $ 1×"], Object.entries(m.by_year).map(([y, r]) => [y, r.trades.toLocaleString("en-US"), pct(r.mean_return_1x), pct(r.mean_return_2x), money(r.net_1x)]))}</div>
    <div class="card"><h2>Round-trip costs, bps of entry notional</h2>${table(["Cost", "bps"], Object.entries(m.cost_bps_of_notional).map(([k, v]) => [k.replace(/_/g, " "), num(v, 1)]))}
    <h2 style="margin-top:12px">From signal to trade</h2>${table(["Stage", "Count"], [["signals", c.signals], ["rejected: capital or duplicate", c.rejected_capital], ["rejected: position too small", c.rejected_size], ["entry never filled", c.unfilled], ["trades", m.trades], ["lookahead replays passed", c.lookahead_checks]].map(([k, v]) => [k, v.toLocaleString("en-US")]))}
    <h2 style="margin-top:12px">Exits</h2>${table(["Reason", "Trades"], Object.entries(m.exit_reasons).sort((p, q) => q[1] - p[1]).map(([k, v]) => [k, v.toLocaleString("en-US")]))}</div></div>`;
  if (d.equity) $("eq").append(lineChart({ labels: d.equity.date, tipTitle: "Cumulative net profit", fmt: (v) => money(v).replace("+", ""),
    series: [{ name: "1× slippage", short: "1×", color: COLORS[0], values: d.equity.cum_net }, { name: "2× slippage", short: "2×", color: COLORS[1], dash: "5 4", values: d.equity.cum_net_2x }] }));
}

function panelStudy(el, d) {
  const s = d.study;
  if (!s || !s.events) { el.innerHTML = header(d.manifest) + `<p class="empty">${s ? "The study found no events." : "This study has not finished."}</p>`; return; }
  const cols = Object.keys(s.curve), lab = (c) => c === "r_close" ? "close" : c.slice(2) + " min";
  const ci = (x) => x.low == null ? pct(x.mean) : `${pct(x.mean)} <span class="dim">(${pct(x.low)} to ${pct(x.high)})</span>`;
  const close = s.curve.r_close, cost = s.mean_cost;
  const split = (title, key) => `<div class="card" style="margin-top:14px"><h2>${title}</h2>${table(["", "Events", "Gross to close", "Net 1× to close (95% interval)", "Net 2× to close", "Net 1× at 60 min"], Object.entries(s[key]).map(([k, g]) => [esc(k), g.r_close.gross.n.toLocaleString("en-US"), pct(g.r_close.gross.mean), ci(g.r_close.net_1x), pct(g.r_close.net_2x.mean), ci(g.r_60.net_1x)]))}</div>`;
  el.innerHTML = header(d.manifest) + `<div class="facts">${fact("Events", s.events.toLocaleString("en-US"), "on " + s.sessions_with_events.toLocaleString("en-US") + " sessions")}
    ${fact("Held to close, net 1×", pct(close.net_1x.mean), `${pct(close.net_1x.low)} to ${pct(close.net_1x.high)}`)}${fact("Net 2×", pct(close.net_2x.mean))}${fact("Gross", pct(close.gross.mean))}
    ${fact("Round-trip cost, 1×", pct(cost.fees + cost.slippage_1x).slice(1), `fees ${pct(cost.fees).slice(1)}, slippage ${pct(cost.slippage_1x).slice(1)}`)}
    ${fact("Median entry price", "$" + num(s.median_entry_price))}${fact("Larger than 5% of the bar", Math.round(100 * s.capacity_limited_share) + "%")}</div>
    <div class="card"><h2>Mean forward return by minutes held after entry</h2><div id="cv"></div><p class="dim">Horizons are not to scale and are capped at the close. The band is the 95% interval for net at 1×, resampling whole sessions.</p></div>
    ${split("By period", "by_period")}${split("By liquidity", "by_liquidity")}${split("By time of the event", "by_time")}${split("By year", "by_year")}`;
  $("cv").append(lineChart({ labels: cols.map(lab), everyLabel: true, tipTitle: "Mean forward return by minutes held", fmt: (v) => pct(v), height: 280,
    band: { low: cols.map((c) => s.curve[c].net_1x.low), high: cols.map((c) => s.curve[c].net_1x.high), color: COLORS[0] },
    series: [{ name: "gross", color: COLORS[2], dash: "1 4", values: cols.map((c) => s.curve[c].gross.mean) }, { name: "net, 1× slippage", short: "net 1×", color: COLORS[0], values: cols.map((c) => s.curve[c].net_1x.mean) }, { name: "net, 2× slippage", short: "net 2×", color: COLORS[1], dash: "5 4", values: cols.map((c) => s.curve[c].net_2x.mean) }] }));
}

async function panelCompare(el) {
  if (!S.compare.length) { el.innerHTML = `<p class="empty">Tick up to four backtests in the Compare column to overlay them.</p>`; return; }
  const ds = await Promise.all(S.compare.map(detail));
  const rows = ds.map((d, i) => { const m = d.metrics, r = S.runs.find((x) => x.run_id === d.manifest.run_id); return [`<span class="key" style="border-color:${COLORS[i]}"></span>${esc(r.config)} <span class="dim">${esc(r.agent)}</span>`, m.trades.toLocaleString("en-US"), pct(m.gross_mean_return), pct(m.slippage_1x.mean_return), pct(m.slippage_2x.mean_return), num(m.slippage_1x.sharpe), money(m.slippage_1x.total_net), money(m.slippage_1x.max_drawdown)]; });
  el.innerHTML = `<div class="card"><h2>Cumulative net profit at 1× slippage, dollars</h2><div id="cmp"></div></div><div class="card" style="margin-top:14px">${table(["Run", "Trades", "Gross / trade", "Net 1×", "Net 2×", "Sharpe", "Total net", "Max drawdown"], rows)}</div>`;
  const base = ds.reduce((a, d) => d.equity.date.length > a.equity.date.length ? d : a).equity.date;
  const same = ds.every((d) => d.equity.date.length === base.length);
  if (!same) { $("cmp").innerHTML = `<p class="dim">These runs cover different sessions, so their curves are not overlaid. The table still compares them.</p>`; return; }
  $("cmp").append(lineChart({ labels: base, tipTitle: "Cumulative net profit by run", fmt: (v) => money(v).replace("+", ""),
    series: ds.map((d, i) => ({ name: S.runs.find((x) => x.run_id === d.manifest.run_id).config, color: COLORS[i], values: d.equity.cum_net })) }));
}

function panelHeatmap(el) {
  const rows = visibleRuns().filter((r) => r.status === "complete" && !r.scratch);
  const keys = [...new Set(rows.flatMap((r) => Object.keys(r.params)))].filter((k) => new Set(rows.map((r) => JSON.stringify(r.params[k]))).size > 1 && !k.startsWith("period"));
  if (keys.length < 1 || rows.length < 2) { el.innerHTML = `<p class="empty">A parameter map needs at least two counted runs${S.family ? " in this family" : ""} that differ in a setting. Pick a family with a sweep, or run more configs.</p>`; return; }
  S.hx = keys.includes(S.hx) ? S.hx : keys[0]; S.hy = keys.includes(S.hy) && S.hy !== S.hx ? S.hy : (keys.find((k) => k !== S.hx) || "");
  S.hm = S.hm || "net_1x";
  const metrics = { net_1x: "Net per trade, 1×", net_2x: "Net per trade, 2×", gross: "Gross per trade", sharpe: "Sharpe", trades: "Trades" };
  const opt = (list, cur) => list.map((k) => `<option value="${esc(k)}" ${k === cur ? "selected" : ""}>${esc(metrics[k] || k.replace(/^params\./, ""))}</option>`).join("");
  const xs = [...new Set(rows.map((r) => r.params[S.hx]))].sort((a, b) => a - b), ys = S.hy ? [...new Set(rows.map((r) => r.params[S.hy]))].sort((a, b) => a - b) : [null];
  const cell = (xv, yv) => rows.filter((r) => r.params[S.hx] === xv && (yv === null || r.params[S.hy] === yv) && r[S.hm] != null);
  const vals = xs.flatMap((xv) => ys.map((yv) => { const c = cell(xv, yv); return c.length ? c.reduce((a, r) => a + r[S.hm], 0) / c.length : null; })).filter((v) => v != null);
  const max = Math.max(...vals.map(Math.abs), 1e-12), isRet = S.hm !== "trades", f = (v) => S.hm === "trades" ? Math.round(v).toLocaleString("en-US") : S.hm === "sharpe" ? num(v) : pct(v);
  const paint = (v) => { const t = Math.min(1, Math.abs(v) / max); return isRet ? `background:color-mix(in oklab, ${v < 0 ? "var(--neg)" : "var(--pos)"} ${Math.round(12 + 60 * t)}%, var(--raise))` : `background:color-mix(in oklab, var(--pos) ${Math.round(12 + 60 * t)}%, var(--raise))`; };
  el.innerHTML = `<p class="note">Show <select id="hm">${opt(Object.keys(metrics), S.hm)}</select> across <select id="hx">${opt(keys, S.hx)}</select> and <select id="hy"><option value="">nothing else</option>${opt(keys.filter((k) => k !== S.hx), S.hy)}</select>. Counted runs only (${rows.length}). Every cell is a trial already charged to its family.</p>
    <div class="card" style="overflow:auto"><table class="hm"><thead><tr><th class="l">${esc(S.hy ? S.hy.replace(/^params\./, "") + " ↓  " : "")}${esc(S.hx.replace(/^params\./, ""))} →</th>${xs.map((v) => `<th>${esc(v)}</th>`).join("")}</tr></thead><tbody>${ys.map((yv) => `<tr style="cursor:default"><th class="l">${yv === null ? "" : esc(yv)}</th>${xs.map((xv) => { const c = cell(xv, yv); if (!c.length) return `<td class="dim">no run</td>`; const v = c.reduce((a, r) => a + r[S.hm], 0) / c.length; return `<td style="${paint(v)}" title="${c.length} run${c.length > 1 ? "s" : ""}: ${esc(c.map((r) => r.config).join(", "))}">${f(v)}${c.length > 1 ? ` <span class="dim">×${c.length}</span>` : ""}</td>`; }).join("")}</tr>`).join("")}</tbody></table></div>
    <p class="dim">${isRet ? "Blue is positive, red is negative; deeper means further from zero." : "Deeper blue means more."} Hover a cell for its runs.</p>`;
  for (const [id, key] of [["hm", "hm"], ["hx", "hx"], ["hy", "hy"]]) $(id).onchange = (e) => { S[key] = e.target.value; panelHeatmap(el); };
}

function panelTrials(el) {
  const fams = S.families.filter((f) => !S.family || f.family === S.family);
  if (!fams.length) { el.innerHTML = `<p class="empty">No runs yet.</p>`; return; }
  el.innerHTML = `<p class="note">Every counted run by any agent is a trial. The more trials a family has, the better its best result must be before it means anything. Scratch runs are shown but never counted.</p>` + fams.map((f) => {
    const o = f.overfitting, agents = Object.entries(f.by_agent).map(([a, n]) => `${esc(a)} ${n}`).join(", ") || "none";
    let body = `<div class="facts">${fact("Trials charged", f.trials, `${f.counted} here + ${f.prior_trials} earlier`)}${fact("Counted runs by agent", agents)}${fact("Scratch runs, not counted", f.scratch)}`;
    if (!o) return `<div class="card" style="margin-bottom:14px"><h2>${esc(f.family)}</h2>${body}</div><p class="dim">No finished backtest in this family yet, so there is no Sharpe to deflate. Event studies add to the count but have no daily P&L.</p></div>`;
    const verdict = o.deflated_sharpe >= 0.95 ? "The best run clears the usual 0.95 bar after charging for the trials." : "The best run does not clear the usual 0.95 bar once the trials are charged.";
    body += `${fact("Best Sharpe, annual", num(o.best_sharpe_annual))}${fact("Sharpe luck alone would show", num(o.expected_max_sharpe_annual), `best of ${f.trials} skill-less tries`)}${fact("Deflated Sharpe", num(o.deflated_sharpe, 3), "probability the true Sharpe is above zero")}${fact("Before deflating", num(o.probabilistic_sharpe, 3))}${fact("Probability of backtest overfitting", o.pbo ? Math.round(100 * o.pbo.pbo) + "%" : "–", o.pbo ? `${o.pbo.trials_compared} runs, ${o.pbo.splits} splits` : "needs 2+ runs over the same sessions")}</div>`;
    const list = Object.entries(o.sharpes).sort((a, b) => b[1] - a[1]).map(([id, s]) => { const r = S.runs.find((x) => x.run_id === id); return [esc(r ? r.config : id), esc(r ? r.agent : ""), num(s), id === o.best_run ? "best" : ""]; });
    return `<div class="card" style="margin-bottom:14px"><h2>${esc(f.family)}</h2>${body}<p class="note">${verdict} ${o.pbo ? `In ${Math.round(100 * o.pbo.pbo)}% of the splits, the run that looked best on one half of the sessions landed in the bottom half on the other.` : ""}</p>${table(["Backtest", "Agent", "Sharpe, annual", ""], list)}</div>`;
  }).join("");
}

$("refresh").onclick = () => { S.detail = {}; load(); };
load();
