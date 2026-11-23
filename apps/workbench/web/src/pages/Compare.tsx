import { useState } from "react";
import { LineChart } from "../components/charts/LineChart";
import { RunsTable, runValue } from "../components/RunsTable";
import { DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel, PanelNote } from "../components/ui/Panel";
import { Segmented } from "../components/ui/Segmented";
import { api, type CompareData, type Metrics, type RunDetail, type RunRow } from "../lib/api";
import { lab, type RunDetail as LabRunDetail } from "../lib/lab";
import { DASHES, SERIES } from "../lib/colors";
import { day, int, money, num, pct, when } from "../lib/format";
import { sortRows, useSort } from "../lib/sort";
import { useLoad } from "../lib/useLoad";
import { useRuns } from "../lib/useRun";

const metrics = (detail: RunDetail) => detail.metrics as Metrics | null | undefined;

function Picker({ ids, runs, onToggle }: { ids: string[]; runs: RunRow[]; onToggle: (run: RunRow) => void }) {
  const [search, setSearch] = useState("");
  const [sort, onSort] = useSort({ key: "started", dir: "desc" });
  const words = search.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const backtests = runs.filter((r) => r.kind === "backtest" && r.status === "complete");
  const shown = sortRows(
    backtests.filter((r) => words.every((w) => `${r.strategy} ${r.config} ${r.run_id} ${r.agent}`.toLowerCase().includes(w))),
    sort,
    runValue,
  );
  return (
    <>
      <div className="border-b border-line px-4 py-2.5">
        <input
          type="search"
          aria-label="Find backtests"
          placeholder="Strategy, config or agent"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="min-h-8 w-64 rounded-md border border-line bg-surface px-2.5 text-[13px] text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none"
        />
      </div>
      <div className="max-h-[420px] overflow-y-auto">
        <RunsTable runs={shown} onOpen={onToggle} compare={ids} onToggleCompare={onToggle} compact sort={sort} onSort={onSort} />
      </div>
    </>
  );
}

function shade(v: number | null): string {
  if (v == null) return "transparent";
  const share = Math.round(Math.min(1, Math.abs(v)) * 60);
  return `color-mix(in srgb, ${v >= 0 ? "var(--series-1)" : "var(--loss)"} ${share}%, var(--surface))`;
}

function Together({ data, names }: { data: CompareData; names: string[] }) {
  const overlap = data.overlap;
  if (!overlap) return null;
  const rows = [...overlap.alone.map((s, i) => ({ name: names[i], slot: i, stats: s })), { name: "Together", slot: -1, stats: overlap.together }];
  return (
    <Panel title="How they move together" aside={`${day(overlap.start)} to ${day(overlap.end)}, the sessions all of them cover`}>
      <div className="grid gap-x-8 gap-y-4 px-4 py-4 lg:grid-cols-[auto_minmax(0,1fr)]">
        <table className="border-collapse text-[13px] tabular-nums">
          <caption className="pb-2 text-left text-[13px] font-semibold text-ink">Correlation of weekly profit</caption>
          <thead>
            <tr>
              <th />
              {names.map((_, i) => (
                <th key={i} className="px-2 pb-1 text-center font-medium text-ink-2">
                  <span aria-hidden="true" className="mr-1 inline-block size-2 rounded-full" style={{ background: SERIES[i] }} />
                  {String.fromCharCode(65 + i)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {overlap.correlation.map((row, i) => (
              <tr key={i}>
                <th scope="row" className="pr-2 text-left font-medium text-ink-2">
                  <span aria-hidden="true" className="mr-1 inline-block size-2 rounded-full" style={{ background: SERIES[i] }} />
                  {String.fromCharCode(65 + i)}
                </th>
                {row.map((v, j) => (
                  <td key={j} className="h-9 w-14 border border-surface text-center" style={{ background: i === j ? "var(--raised)" : shade(v) }}>
                    {i === j ? "" : v == null ? "–" : num(v, 2)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        <DataTable
          rows={rows}
          rowKey={(r) => String(r.slot)}
          columns={[
            {
              key: "name",
              header: "Over the shared sessions",
              align: "left",
              strong: true,
              render: (r) => (r.slot < 0 ? "Together, each at its own size" : `${String.fromCharCode(65 + r.slot)}  ${r.name}`),
            },
            { key: "total", header: "Net profit", signed: true, render: (r) => money(r.stats.total) },
            { key: "sharpe", header: "Sharpe", signed: true, render: (r) => num(r.stats.sharpe, 2) },
            { key: "dd", header: "Worst drawdown", signed: true, render: (r) => money(r.stats.worst_drawdown) },
          ]}
        />
      </div>
      <PanelNote>
        {int(overlap.weeks)} weeks of five sessions. Runs that rarely lose in the same weeks (a correlation near zero or below) make a steadier book together than either alone; two variants of one
        rule usually move as one.
      </PanelNote>
    </Panel>
  );
}

interface Row {
  id: string;
  source: "Backtest" | "Lab";
  name: string;
  detail: string;
  period: string;
  trades?: number | null;
  gross?: number | null;
  n1?: number | null;
  n2?: number | null;
  t?: number | null;
  total?: number | null;
  dd?: number | null;
}

export const isLab = (id: string) => id.startsWith("lab:");

function backtestRow(detail: RunDetail): Row {
  const m = metrics(detail);
  return {
    id: detail.manifest.run_id,
    source: "Backtest",
    name: detail.manifest.strategy,
    detail: detail.manifest.config,
    period: `${detail.manifest.period.start.slice(0, 4)}–${detail.manifest.period.end.slice(0, 4)}`,
    trades: m?.trades,
    gross: m?.gross_mean_return,
    n1: m?.slippage_1x.mean_return,
    n2: m?.slippage_2x.mean_return,
    t: m?.slippage_2x.t_stat_daily,
    total: m?.slippage_1x.total_net,
    dd: m?.slippage_1x.max_drawdown,
  };
}

export function labRow(id: string, run: LabRunDetail): Row {
  const s = run.summary;
  return {
    id,
    source: "Lab",
    name: run.manifest?.algorithm ?? id.slice(4),
    detail: `Lab run, ${when(run.manifest?.created_at ?? "")}`,
    period: s?.period_label ?? "–",
    trades: s?.trades,
    gross: s?.mean_gross,
    n1: s?.mean_net,
    n2: s?.mean_net_2x,
    t: s?.t_weekly_2x,
    total: s?.book_profit,
    dd: s?.max_drawdown,
  };
}

function LabPicker({ ids, onToggle }: { ids: string[]; onToggle: (id: string) => void }) {
  const { data } = useLoad(() => lab.runs(), "compare-lab-runs");
  const runs = (data ?? []).filter((r) => r.state === "complete" && (r.trades ?? 0) > 0);
  if (!data) return <p className="m-0 px-4 py-6 text-ink-2">Loading the Lab runs…</p>;
  return (
    <DataTable
      rows={runs}
      rowKey={(r) => r.run_id}
      onRowClick={(r) => onToggle(`lab:${r.run_id}`)}
      empty="No finished Lab runs with trades yet."
      columns={[
        {
          key: "pick",
          header: "Compare",
          align: "left",
          render: (r) => <input type="checkbox" readOnly checked={ids.includes(`lab:${r.run_id}`)} aria-label={`Compare ${r.algorithm}`} tabIndex={-1} />,
        },
        { key: "algorithm", header: "Algorithm", align: "left", strong: true, render: (r) => r.algorithm },
        { key: "period", header: "Period", align: "left", muted: true, render: (r) => r.period ?? "–" },
        { key: "created", header: "Started", muted: true, render: (r) => when(r.created_at) },
        { key: "trades", header: "Trades", render: (r) => int(r.trades) },
        { key: "mean_net", header: "A trade", signed: true, render: (r) => pct(r.mean_net) },
        { key: "book_profit", header: "Book profit", signed: true, render: (r) => money(r.book_profit) },
      ]}
    />
  );
}

export function Compare({ ids, runs, onToggle }: { ids: string[]; runs: RunRow[]; onToggle: (id: string) => void }) {
  const [source, setSource] = useState<"backtests" | "lab">(ids.some(isLab) && !ids.some((id) => !isLab(id)) ? "lab" : "backtests");
  const backtests = ids.filter((id) => !isLab(id));
  const labIds = ids.filter(isLab);
  const details = useRuns(backtests);
  const { data: labDetails } = useLoad(() => Promise.all(labIds.map((id) => lab.run(id.slice(4)))), `compare-lab-${labIds.join(",")}`);
  const { data: together } = useLoad(() => (ids.length ? api.compare(ids) : Promise.resolve(null)), `compare-${ids.join(",")}`);
  const picker = (
    <Panel
      title={`Runs to compare, ${ids.length} of 4 picked`}
      aside={
        <Segmented
          label="Runs to pick from"
          value={source}
          onChange={setSource}
          options={[
            { value: "backtests", label: "Backtests" },
            { value: "lab", label: "Lab runs" },
          ]}
        />
      }
    >
      {source === "backtests" ? <Picker ids={ids} runs={runs} onToggle={(run) => onToggle(run.run_id)} /> : <LabPicker ids={ids} onToggle={onToggle} />}
    </Panel>
  );
  if (!ids.length)
    return (
      <>
        <EmptyState title="Nothing to compare yet">Pick up to four backtests or Lab runs below, or tick backtests in the Compare column of the runs table.</EmptyState>
        {picker}
      </>
    );
  if (!details || (labIds.length && !labDetails)) return <p className="text-ink-2">Loading the runs…</p>;
  const byId = new Map<string, Row>([...details.map((d) => [d.manifest.run_id, backtestRow(d)] as const), ...labIds.map((id, i) => [id, labRow(id, labDetails![i])] as const)]);
  const rows = ids.map((id) => byId.get(id)).filter((r): r is Row => Boolean(r));
  const curves = together && together.runs.length === rows.length ? together : null;
  const slot = (id: string) => (curves ? curves.runs.findIndex((r) => r.run_id === id) : rows.findIndex((r) => r.id === id));
  const names = (curves?.runs ?? []).map((r) => {
    const row = byId.get(r.run_id);
    return row ? `${row.name}, ${row.source === "Lab" ? `Lab, ${row.period}` : row.detail}` : r.run_id;
  });
  const drawn = (curves?.runs ?? []).some((r) => r.lab && !r.lab.daily);
  const legend = (row: Row) => {
    const base = row.source === "Lab" ? `${row.name} (Lab)` : row.name;
    return rows.filter((r) => r.name === row.name && r.source === row.source).length > 1 ? `${base}, ${row.source === "Lab" ? row.period : row.detail}` : base;
  };
  return (
    <>
      <Panel title="Cumulative net profit at 1× slippage, dollars">
        {curves && curves.dates.length ? (
          <LineChart
            title="Cumulative net profit of the selected runs"
            labels={curves.dates}
            format={(v) => money(v).replace("+", "")}
            series={[
              ...rows.map((row) => ({ name: legend(row), values: curves.curves[slot(row.id)], color: SERIES[slot(row.id)], dash: DASHES[slot(row.id)] })),
              ...(rows.length > 1 && curves.together ? [{ name: "Together", short: "Together", values: curves.together, color: "var(--ink)", dash: "1 3" }] : []),
            ]}
          />
        ) : (
          <p className="m-0 px-4 py-6 text-ink-2">Loading the curves…</p>
        )}
        {rows.length > 1 && curves && !curves.overlap && <PanelNote>These runs share no sessions, so they are drawn on one calendar but not measured together.</PanelNote>}
        {drawn && <PanelNote>A Lab run from before 23 Nov keeps only its drawn curve, so its weeks are approximate; run it again for its full daily book.</PanelNote>}
      </Panel>
      {curves?.overlap && rows.length > 1 && <Together data={curves} names={names} />}
      <Panel title="Side by side">
        <DataTable
          rows={rows}
          rowKey={(r) => r.id}
          minWidth={900}
          columns={[
            { key: "name", header: "Run", align: "left", strong: true, render: (r) => r.name },
            { key: "detail", header: "", align: "left", muted: true, max: 220, render: (r) => (r.source === "Lab" ? "Lab" : r.detail) },
            { key: "period", header: "Period", align: "left", muted: true, render: (r) => r.period },
            { key: "trades", header: "Trades", render: (r) => int(r.trades) },
            { key: "gross", header: "Gross", signed: true, render: (r) => pct(r.gross) },
            { key: "n1", header: "Net 1×", signed: true, strong: true, render: (r) => pct(r.n1) },
            { key: "n2", header: "Net 2×", signed: true, render: (r) => pct(r.n2) },
            { key: "t2", header: "t at 2×", signed: true, render: (r) => num(r.t) },
            { key: "total", header: "Total net", signed: true, render: (r) => money(r.total) },
            { key: "dd", header: "Worst drawdown", signed: true, render: (r) => money(r.dd) },
            {
              key: "remove",
              header: "",
              render: (r) => (
                <button type="button" onClick={() => onToggle(r.id)} className="cursor-pointer text-[13px] font-medium text-ink-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-accent">
                  Remove
                </button>
              ),
            },
          ]}
        />
        {rows.some((r) => r.source === "Lab") && (
          <PanelNote>
            Backtests and Lab runs are measured their own ways: a backtest&apos;s t is on daily profit, a Lab run&apos;s on weekly trade returns; a Lab run&apos;s total is its book&apos;s profit at
            its position size. The curves above put both on the same calendar.
          </PanelNote>
        )}
      </Panel>
      {picker}
    </>
  );
}
