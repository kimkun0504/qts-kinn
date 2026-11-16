import { useState } from "react";
import { LineChart } from "../components/charts/LineChart";
import { RunsTable } from "../components/RunsTable";
import { StateBadge, TargetsBadge, targetsText } from "../components/Verdict";
import { Badge } from "../components/ui/Badge";
import { DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel, PanelNote } from "../components/ui/Panel";
import { Segmented } from "../components/ui/Segmented";
import { StatStrip } from "../components/ui/StatStrip";
import type { Family, RunRow, StrategyInfo } from "../lib/api";
import { DASHES, SERIES } from "../lib/colors";
import { int, money, num, pct } from "../lib/format";
import { useRun } from "../lib/useRun";

interface OverviewProps {
  runs: RunRow[];
  families: Family[];
  strategies: StrategyInfo[];
  onOpen: (run: RunRow) => void;
}

type StateFilter = "all" | "candidate" | "developing" | "parked";

export function Overview({ runs, families, strategies, onOpen }: OverviewProps) {
  const [state, setState] = useState<StateFilter>("all");
  const counted = runs.filter((r) => r.status === "complete" && !r.scratch);
  const ready = strategies.filter((s) => s.ready_for_paper);
  const lead = ready[0] ?? strategies.find((s) => s.candidate_run) ?? null;
  // The headline is the candidate's out-of-sample run. With no candidate, the newest backtest.
  const latest = counted.find((r) => r.kind === "backtest" && !r.family.startsWith("canary")) ?? counted.find((r) => r.kind === "backtest") ?? null;
  const featured = lead?.candidate_run ?? latest;
  const { detail } = useRun(featured?.run_id ?? null);
  if (!runs.length)
    return <EmptyState title="No runs yet">Start one with: uv run kinn run &lt;strategy&gt; --config &lt;name&gt;. It will appear here after a reload.</EmptyState>;
  const trials = families.reduce((sum, f) => sum + f.trials, 0);
  const shown = strategies.filter((s) => state === "all" || s.state === state);
  const targets = featured?.targets ?? null;
  return (
    <>
      <StatStrip
        items={
          lead && featured
            ? [
                { label: "Candidate for paper trading", value: lead.strategy, note: `${featured.config}, ${featured.period.start} to ${featured.period.end}` },
                { label: "Net per trade at 2× slippage", value: pct(featured.net_2x), note: "target: at least +1.00%" },
                { label: "Sharpe at 2× slippage", value: num(featured.sharpe_2x), note: "target: above 1.00" },
                { label: "Worst drawdown at 2×", value: money(featured.drawdown_2x), note: "target: under half the account" },
                {
                  label: "Targets met",
                  value: targets ? `${targets.met} of ${targets.of}` : "–",
                  note: lead.ready_for_paper ? "fills confirmed; ready for paper trading" : targets ? `fills ${targets.fills}` : "not judged",
                },
              ]
            : [
                { label: "Candidate for paper trading", value: "None yet", note: "no strategy.yaml names a candidate" },
                { label: "Runs in the store", value: int(runs.length), note: `${int(counted.length)} finished and counted` },
                { label: "Trials charged", value: int(trials) },
                featured
                  ? { label: "Latest backtest, net per trade", value: pct(featured.net_1x), note: `${featured.strategy} ${featured.config}; 2× ${pct(featured.net_2x)}` }
                  : { label: "Latest backtest", value: "–", note: "none finished yet" },
              ]
        }
      />
      {ready.length > 0 && (
        <Panel title="Ready for paper trading" aside="met all four targets out of sample">
          <DataTable
            rows={ready}
            rowKey={(s) => s.strategy}
            onRowClick={(s) => s.candidate_run && onOpen(s.candidate_run)}
            columns={[
              { key: "strategy", header: "Strategy", align: "left", strong: true, render: (s) => s.strategy },
              { key: "config", header: "Frozen config", align: "left", render: (s) => s.candidate_config },
              { key: "code", header: "Code", align: "left", muted: true, render: (s) => s.candidate_run?.commit },
              { key: "data", header: "Data build", align: "left", muted: true, render: (s) => s.candidate_run?.data_build_id },
              { key: "net", header: "Net 2×", signed: true, render: (s) => pct(s.candidate_run?.net_2x) },
              { key: "sharpe", header: "Sharpe 2×", render: (s) => num(s.candidate_run?.sharpe_2x) },
              { key: "dd", header: "Worst drawdown 2×", signed: true, render: (s) => money(s.candidate_run?.drawdown_2x) },
              { key: "total", header: "Total net 2×", signed: true, render: (s) => money(s.candidate_run?.total_net_2x) },
              { key: "fills", header: "Fills", align: "left", render: () => <Badge tone="ok">Confirmed</Badge> },
            ]}
          />
          <PanelNote>
            This is the exact version a paper-trading app would run: the config, the code commit and the data build of its validation run. That app is not built yet, and
            nothing in the Workbench places orders. The holdout has not been used.
          </PanelNote>
        </Panel>
      )}
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(440px,1fr)]">
        <Panel
          title={featured ? `${lead ? "Candidate: " : "Latest backtest: "}${featured.strategy} ${featured.config}, cumulative net profit` : "Cumulative net profit"}
          aside={featured ? `${featured.period.start} to ${featured.period.end}` : undefined}
        >
          {detail?.equity ? (
            <LineChart
              title="Cumulative net profit at 1x and 2x slippage"
              labels={detail.equity.date}
              format={(v) => money(v).replace("+", "")}
              series={[
                { name: "1× slippage", short: "1×", values: detail.equity.cum_net, color: SERIES[0] },
                { name: "2× slippage", short: "2×", values: detail.equity.cum_net_2x, color: SERIES[1], dash: DASHES[1] },
              ]}
            />
          ) : (
            <PanelNote>{featured ? "Loading the run…" : "No finished backtest yet."}</PanelNote>
          )}
        </Panel>
        <Panel
          title={`Strategies (${shown.length})`}
          aside={
            <Segmented
              label="Strategy status"
              value={state}
              onChange={setState}
              options={[
                { value: "all", label: "All" },
                { value: "candidate", label: "Candidates" },
                { value: "developing", label: "Developing" },
                { value: "parked", label: "Parked" },
              ]}
            />
          }
        >
          <DataTable
            rows={shown}
            rowKey={(s) => s.strategy}
            onRowClick={(s) => {
              const run = s.validation_run ?? runs.find((r) => r.strategy === s.strategy);
              if (run) onOpen(run);
            }}
            empty="No strategy has this status."
            columns={[
              { key: "strategy", header: "Strategy", align: "left", strong: true, render: (s) => s.strategy },
              { key: "state", header: "Status", align: "left", render: (s) => <StateBadge state={s.state} /> },
              { key: "owner", header: "Owner", align: "left", muted: true, render: (s) => s.owner ?? "–" },
              { key: "runs", header: "Runs", muted: true, render: (s) => int(s.runs) },
              { key: "net", header: "Validation net 2×", signed: true, render: (s) => pct(s.validation_run?.net_2x) },
              {
                key: "targets",
                header: "Targets",
                align: "left",
                render: (s) => (s.validation_run?.targets && s.state !== "canary" ? <TargetsBadge targets={s.validation_run.targets} /> : "–"),
              },
            ]}
          />
          <PanelNote>
            Status and candidate come from each strategy.yaml; the reasons are in its REPORT.md. Targets are judged on validation runs only (2017 to 2023): net per trade at 2×
            of at least +1%, Sharpe above 1, drawdown under half the account, and fills confirmed against real trades.
            {lead?.candidate_run?.targets ? ` ${lead.strategy}: ${targetsText(lead.candidate_run.targets)}.` : ""}
          </PanelNote>
        </Panel>
      </div>
      <div className="grid gap-4 xl:grid-cols-[minmax(0,1.5fr)_minmax(440px,1fr)]">
        <Panel title="Recent runs" aside={`${int(runs.length)} in the store`}>
          <RunsTable runs={runs.slice(0, 8)} onOpen={onOpen} compact />
        </Panel>
        <Panel title="Trials by family" aside={`${int(trials)} charged`}>
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
