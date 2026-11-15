import { LineChart } from "../components/charts/LineChart";
import { DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel, PanelNote } from "../components/ui/Panel";
import type { Metrics, RunDetail, RunRow } from "../lib/api";
import { DASHES, SERIES } from "../lib/colors";
import { int, money, num, pct } from "../lib/format";
import { useRuns } from "../lib/useRun";

/** Only backtests can be ticked for comparison, so the metrics here are a backtest's. */
const metrics = (detail: RunDetail) => detail.metrics as Metrics | null | undefined;

export function Compare({ ids, runs }: { ids: string[]; runs: RunRow[] }) {
  const details = useRuns(ids);
  if (!ids.length) return <EmptyState title="Nothing to compare yet">Tick up to four backtests in the Compare column of the runs table.</EmptyState>;
  if (!details) return <p className="text-ink-2">Loading the runs…</p>;
  const rows = details.map((d, i) => ({ detail: d, row: runs.find((r) => r.run_id === d.manifest.run_id), slot: i }));
  const length = details[0].equity?.date.length ?? 0;
  const same = details.every((d) => d.equity && d.equity.date.length === length && d.equity.date[0] === details[0].equity?.date[0]);
  return (
    <>
      <Panel title="Cumulative net profit at 1× slippage, dollars">
        {same && details[0].equity ? (
          <LineChart
            title="Cumulative net profit of the selected backtests"
            labels={details[0].equity.date}
            format={(v) => money(v).replace("+", "")}
            series={rows.map(({ detail, slot }) => ({ name: detail.manifest.config, values: detail.equity?.cum_net ?? [], color: SERIES[slot], dash: DASHES[slot] }))}
          />
        ) : (
          <PanelNote>These runs cover different sessions, so their curves are not overlaid. The table still compares them.</PanelNote>
        )}
      </Panel>
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
          ]}
        />
      </Panel>
    </>
  );
}
