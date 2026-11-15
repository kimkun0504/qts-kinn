import { useState } from "react";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel, PanelNote } from "../components/ui/Panel";
import type { RunRow } from "../lib/api";
import { int, num, pct } from "../lib/format";

type Metric = "net_1x" | "net_2x" | "gross" | "t_stat_2x" | "trades";
const METRICS: Record<Metric, string> = { net_1x: "Net per trade, 1×", net_2x: "Net per trade, 2×", gross: "Gross per trade", t_stat_2x: "t-statistic at 2×", trades: "Trades" };
const clean = (key: string) => key.replace(/^params\./, "").replace(/_/g, " ");

function Select({ label, value, options, onChange }: { label: string; value: string; options: [string, string][]; onChange: (value: string) => void }) {
  return (
    <label className="inline-flex items-center gap-2 text-ink-2">
      {label}
      <select value={value} onChange={(event) => onChange(event.target.value)} className="min-h-8 rounded-md border border-line bg-surface px-2 text-[13px] text-ink">
        {options.map(([key, text]) => (
          <option key={key} value={key}>
            {text}
          </option>
        ))}
      </select>
    </label>
  );
}

/** A grid of one result across one or two settings that differ between counted runs. */
export function Parameters({ runs }: { runs: RunRow[] }) {
  const rows = runs.filter((r) => r.status === "complete" && !r.scratch && r.kind === "backtest");
  const periods = [...new Set(rows.map((r) => `${r.period.start} to ${r.period.end}`))];
  const [period, setPeriod] = useState<string>("");
  const inPeriod = rows.filter((r) => `${r.period.start} to ${r.period.end}` === (period || periods[0]));
  const keys = [...new Set(inPeriod.flatMap((r) => Object.keys(r.params)))].filter(
    (key) => key.startsWith("params.") && new Set(inPeriod.map((r) => JSON.stringify(r.params[key] ?? null))).size > 1,
  );
  const [xKey, setX] = useState("");
  const [yKey, setY] = useState("");
  const [metric, setMetric] = useState<Metric>("net_1x");
  if (inPeriod.length < 2 || !keys.length)
    return <EmptyState title="A parameter map needs a sweep">Pick a family in the side rail with at least two counted backtests that differ in a setting.</EmptyState>;
  const x = keys.includes(xKey) ? xKey : keys[0];
  const y = keys.includes(yKey) && yKey !== x ? yKey : (keys.find((k) => k !== x) ?? "");
  const order = (a: unknown, b: unknown) => (typeof a === "number" && typeof b === "number" ? a - b : String(a).localeCompare(String(b)));
  const xs = [...new Set(inPeriod.map((r) => r.params[x] ?? null))].sort(order);
  const ys = y ? [...new Set(inPeriod.map((r) => r.params[y] ?? null))].sort(order) : [null];
  const cell = (xv: unknown, yv: unknown) => inPeriod.filter((r) => (r.params[x] ?? null) === xv && (!y || (r.params[y] ?? null) === yv) && r[metric] != null);
  const mean = (list: RunRow[]) => list.reduce((sum, r) => sum + (r[metric] as number), 0) / list.length;
  const values = xs.flatMap((xv) => ys.map((yv) => cell(xv, yv))).filter((c) => c.length).map(mean);
  const max = Math.max(...values.map(Math.abs), 1e-12);
  const format = (v: number) => (metric === "trades" ? int(v) : metric === "t_stat_2x" ? num(v) : pct(v));
  const paint = (v: number) => {
    const strength = Math.round(10 + 55 * Math.min(1, Math.abs(v) / max));
    const hue = metric !== "trades" && v < 0 ? "var(--neg)" : "var(--accent)";
    return { background: `color-mix(in oklab, ${hue} ${strength}%, var(--raised))` };
  };
  const show = (v: unknown) => (v === null ? "off" : String(v));
  return (
    <>
      <div className="flex flex-wrap items-center gap-4">
        <Select label="Show" value={metric} options={Object.entries(METRICS) as [string, string][]} onChange={(v) => setMetric(v as Metric)} />
        <Select label="across" value={x} options={keys.map((k) => [k, clean(k)])} onChange={setX} />
        <Select label="and" value={y} options={[["", "nothing else"], ...keys.filter((k) => k !== x).map((k): [string, string] => [k, clean(k)])]} onChange={setY} />
        {periods.length > 1 && <Select label="period" value={period || periods[0]} options={periods.map((p) => [p, p])} onChange={setPeriod} />}
      </div>
      <Panel title={`${METRICS[metric]} by ${clean(x)}${y ? ` and ${clean(y)}` : ""}`} aside={`${inPeriod.length} counted backtests`}>
        <table className="border-collapse">
          <thead>
            <tr>
              <th scope="col" className="px-3 py-2 text-left text-xs font-medium text-ink-2">
                {y ? `${clean(y)} ↓ ` : ""}
                {clean(x)} →
              </th>
              {xs.map((xv) => (
                <th key={show(xv)} scope="col" className="px-3 py-2 text-center text-xs font-medium text-ink-2">
                  {show(xv)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ys.map((yv) => (
              <tr key={show(yv)}>
                <th scope="row" className="px-3 py-2 text-left text-xs font-medium text-ink-2">
                  {y ? show(yv) : ""}
                </th>
                {xs.map((xv) => {
                  const list = cell(xv, yv);
                  if (!list.length)
                    return (
                      <td key={show(xv)} className="min-w-[88px] border-2 border-surface px-3 py-2.5 text-center text-ink-3">
                        no run
                      </td>
                    );
                  const v = mean(list);
                  return (
                    <td key={show(xv)} title={list.map((r) => r.config).join(", ")} style={paint(v)} className="min-w-[88px] border-2 border-surface px-3 py-2.5 text-center font-medium">
                      {format(v)}
                      {list.length > 1 && <span className="text-ink-2"> ×{list.length}</span>}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
        <PanelNote>
          Every cell is a trial already charged to its family. Cells that share both settings are averaged. Blue is positive, red is negative, and deeper means further from zero.
        </PanelNote>
      </Panel>
    </>
  );
}
