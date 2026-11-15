import { LineChart } from "../components/charts/LineChart";
import { RunsTable } from "../components/RunsTable";
import { DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel, PanelNote } from "../components/ui/Panel";
import { StatStrip } from "../components/ui/StatStrip";
import type { Family, RunRow } from "../lib/api";
import { DASHES, SERIES } from "../lib/colors";
import { int, money, num, pct } from "../lib/format";
import { useRun } from "../lib/useRun";

interface OverviewProps {
  runs: RunRow[];
  families: Family[];
  onOpen: (run: RunRow) => void;
}

interface StrategyRow {
  strategy: string;
  runs: number;
  latest: RunRow;
  best: RunRow | null;
}

function strategies(runs: RunRow[]): StrategyRow[] {
  const map = new Map<string, RunRow[]>();
  for (const run of runs) if (run.status === "complete" && !run.scratch) map.set(run.strategy, [...(map.get(run.strategy) ?? []), run]);
  return [...map.entries()].map(([strategy, list]) => {
    const scored = list.filter((r) => r.t_stat_2x != null);
    return {
      strategy,
      runs: list.length,
      latest: list[0],
      best: scored.length ? scored.reduce((a, b) => ((b.t_stat_2x ?? -99) > (a.t_stat_2x ?? -99) ? b : a)) : null,
    };
  });
}

export function Overview({ runs, families, onOpen }: OverviewProps) {
  const complete = runs.filter((r) => r.status === "complete");
  const counted = complete.filter((r) => !r.scratch);
  // The featured chart: the newest finished, counted backtest outside the canary families.
  const featured = counted.find((r) => r.kind === "backtest" && !r.family.startsWith("canary")) ?? counted.find((r) => r.kind === "backtest") ?? null;
  const { detail } = useRun(featured?.run_id ?? null);
  if (!runs.length)
    return <EmptyState title="No runs yet">Start one with: uv run kinn run &lt;strategy&gt; --config &lt;name&gt;. It will appear here after a reload.</EmptyState>;
  const trials = families.reduce((sum, f) => sum + f.trials, 0);
  return (
    <>
      <StatStrip
        items={[
          { label: "Runs in the store", value: int(runs.length), note: `${int(counted.length)} finished and counted` },
          { label: "Trials charged", value: int(trials), note: families.map((f) => `${f.family} ${f.trials}`).join(", ") },
          featured
            ? { label: "Latest backtest, net per trade", value: pct(featured.net_1x), note: `${featured.strategy} ${featured.config}; 2× ${pct(featured.net_2x)}` }
            : { label: "Latest backtest", value: "–", note: "none finished yet" },
          featured
            ? { label: "Its total net", value: money(featured.total_net), note: `t at 2× slippage ${num(featured.t_stat_2x)}` }
            : { label: "Total net", value: "–" },
        ]}
      />
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(440px,1fr)]">
        <Panel title={featured ? `${featured.strategy} ${featured.config}: cumulative net profit, dollars` : "Cumulative net profit"} aside={featured ? `${featured.period.start} to ${featured.period.end}` : undefined}>
          {detail?.equity ? (
            <LineChart
              title="Cumulative net profit of the latest backtest at 1x and 2x slippage"
              labels={detail.equity.date}
              format={(v) => money(v).replace("+", "")}
              series={[
                { name: "1× slippage", short: "1×", values: detail.equity.cum_net, color: SERIES[0] },
                { name: "2× slippage", short: "2×", values: detail.equity.cum_net_2x, color: SERIES[1], dash: DASHES[1] },
              ]}
            />
          ) : (
            <PanelNote>{featured ? "Loading the latest backtest…" : "No finished backtest yet."}</PanelNote>
          )}
        </Panel>
        <Panel title="Strategies" aside="counted runs only">
          <DataTable
            rows={strategies(runs)}
            rowKey={(r) => r.strategy}
            onRowClick={(r) => onOpen(r.best ?? r.latest)}
            columns={[
              { key: "strategy", header: "Strategy", align: "left", strong: true, render: (r) => r.strategy },
              { key: "runs", header: "Runs", muted: true, render: (r) => int(r.runs) },
              { key: "net", header: "Latest net 1×", signed: true, render: (r) => pct(r.latest.net_1x) },
              { key: "best", header: "Best t at 2×", signed: true, render: (r) => num(r.best?.t_stat_2x) },
            ]}
          />
          <PanelNote>A strategy's verdict lives in its REPORT.md. The best t-statistic is before charging for trials; see Trials.</PanelNote>
        </Panel>
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(440px,1fr)]">
        <Panel title="Recent runs" aside={`${int(runs.length)} in the store`}>
          <RunsTable runs={runs.slice(0, 8)} onOpen={onOpen} compact />
        </Panel>
        <Panel title="Trials by family">
          <DataTable
            rows={families}
            rowKey={(f) => f.family}
            columns={[
              { key: "family", header: "Family", align: "left", render: (f) => f.family },
              { key: "trials", header: "Trials", strong: true, render: (f) => int(f.trials) },
              { key: "here", header: "Runs here", muted: true, render: (f) => int(f.counted) },
              { key: "prior", header: "Earlier", muted: true, render: (f) => int(f.prior_trials) },
              { key: "dsr", header: "Deflated SR", render: (f) => num(f.overfitting?.deflated_sharpe, 3) },
            ]}
          />
        </Panel>
      </div>
    </>
  );
}
