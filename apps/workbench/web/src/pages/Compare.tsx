import { useState } from "react";
import { LineChart } from "../components/charts/LineChart";
import { RunsTable, runValue } from "../components/RunsTable";
import { DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel, PanelNote } from "../components/ui/Panel";
import { api, type CompareData, type Metrics, type RunDetail, type RunRow } from "../lib/api";
import { DASHES, SERIES } from "../lib/colors";
import { day, int, money, num, pct } from "../lib/format";
import { sortRows, useSort } from "../lib/sort";
import { useLoad } from "../lib/useLoad";
import { useRuns } from "../lib/useRun";

/** Only backtests can be ticked for comparison, so the metrics here are a backtest's. */
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
    <Panel
      title={`Backtests to compare, ${ids.length} of 4 picked`}
      aside={
        <input
          type="search"
          aria-label="Find backtests"
          placeholder="Strategy, config or agent"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="min-h-8 w-56 rounded-md border border-line bg-surface px-2.5 text-[13px] text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none"
        />
      }
    >
      <div className="max-h-[420px] overflow-y-auto">
        <RunsTable runs={shown} onOpen={onToggle} compare={ids} onToggleCompare={onToggle} compact sort={sort} onSort={onSort} />
      </div>
    </Panel>
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

export function Compare({ ids, runs, onToggle }: { ids: string[]; runs: RunRow[]; onToggle: (run: RunRow) => void }) {
  const details = useRuns(ids);
  const { data: together } = useLoad(() => (ids.length ? api.compare(ids) : Promise.resolve(null)), `compare-${ids.join(",")}`);
  if (!ids.length)
    return (
      <>
        <EmptyState title="Nothing to compare yet">Pick up to four backtests below, or tick them in the Compare column of the runs table.</EmptyState>
        <Picker ids={ids} runs={runs} onToggle={onToggle} />
      </>
    );
  if (!details) return <p className="text-ink-2">Loading the runs…</p>;
  const rows = details.map((d, i) => ({ detail: d, row: runs.find((r) => r.run_id === d.manifest.run_id), slot: i }));
  const names = rows.map(({ detail }) => `${detail.manifest.strategy}, ${detail.manifest.config}`);
  const curves = together && together.runs.length === details.length ? together : null;
  return (
    <>
      <Panel title="Cumulative net profit at 1× slippage, dollars">
        {curves && curves.dates.length ? (
          <LineChart
            title="Cumulative net profit of the selected backtests"
            labels={curves.dates}
            format={(v) => money(v).replace("+", "")}
            series={[
              ...rows.map(({ detail, slot }) => ({ name: detail.manifest.config, values: curves.curves[slot], color: SERIES[slot], dash: DASHES[slot] })),
              ...(rows.length > 1 && curves.together ? [{ name: "Together", short: "Together", values: curves.together, color: "var(--ink-2)", dash: "2 2" }] : []),
            ]}
          />
        ) : (
          <p className="m-0 px-4 py-6 text-ink-2">Loading the curves…</p>
        )}
        {rows.length > 1 && curves && !curves.overlap && <PanelNote>These runs share no sessions, so they are drawn on one calendar but not measured together.</PanelNote>}
      </Panel>
      {curves?.overlap && rows.length > 1 && <Together data={curves} names={names} />}
      <Panel title="Side by side">
        <DataTable
          rows={rows}
          rowKey={(r) => r.detail.manifest.run_id}
          minWidth={820}
          columns={[
            { key: "config", header: "Config", align: "left", strong: true, render: (r) => r.detail.manifest.config },
            { key: "period", header: "Period", align: "left", muted: true, render: (r) => `${r.detail.manifest.period.start.slice(0, 4)}–${r.detail.manifest.period.end.slice(0, 4)}` },
            { key: "trades", header: "Trades", render: (r) => int(metrics(r.detail)?.trades) },
            { key: "gross", header: "Gross", signed: true, render: (r) => pct(metrics(r.detail)?.gross_mean_return) },
            { key: "n1", header: "Net 1×", signed: true, strong: true, render: (r) => pct(metrics(r.detail)?.slippage_1x.mean_return) },
            { key: "n2", header: "Net 2×", signed: true, render: (r) => pct(metrics(r.detail)?.slippage_2x.mean_return) },
            { key: "t2", header: "t at 2×", signed: true, render: (r) => num(metrics(r.detail)?.slippage_2x.t_stat_daily) },
            { key: "total", header: "Total net", signed: true, render: (r) => money(metrics(r.detail)?.slippage_1x.total_net) },
            { key: "dd", header: "Worst drawdown", signed: true, render: (r) => money(metrics(r.detail)?.slippage_1x.max_drawdown) },
            {
              key: "remove",
              header: "",
              render: (r) =>
                r.row ? (
                  <button
                    type="button"
                    onClick={() => r.row && onToggle(r.row)}
                    className="cursor-pointer text-[13px] font-medium text-ink-2 hover:text-ink focus-visible:outline-2 focus-visible:outline-accent"
                  >
                    Remove
                  </button>
                ) : null,
            },
          ]}
        />
      </Panel>
      <Picker ids={ids} runs={runs} onToggle={onToggle} />
    </>
  );
}
