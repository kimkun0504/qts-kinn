import { DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel, PanelNote } from "../components/ui/Panel";
import { StatStrip } from "../components/ui/StatStrip";
import type { Family, RunRow } from "../lib/api";
import { int, num, plainPct } from "../lib/format";

export function Trials({ families, runs }: { families: Family[]; runs: RunRow[] }) {
  if (!families.length) return <EmptyState title="No runs yet" />;
  return (
    <>
      <p className="m-0 max-w-[80ch] text-ink-2">
        Every counted run by any agent is a trial. The more trials a family has, the better its best result must be before it means anything. Scratch and abandoned runs are never counted.
      </p>
      {families.map((family) => {
        const o = family.overfitting;
        const agents = Object.entries(family.by_agent).map(([agent, n]) => `${agent} ${n}`).join(", ") || "none";
        const sharpes = o ? Object.entries(o.sharpes).map(([id, sharpe]) => ({ id, sharpe, run: runs.find((r) => r.run_id === id) })).sort((a, b) => b.sharpe - a.sharpe) : [];
        return (
          <Panel key={family.family} title={family.family} aside={`${int(family.runs)} run folders`}>
            <div className="p-4">
              <StatStrip
                items={[
                  { label: "Trials charged", value: int(family.trials), note: `${family.counted} here + ${family.prior_trials} earlier` },
                  { label: "Counted runs by agent", value: agents },
                  { label: "Not counted", value: int(family.scratch + family.abandoned), note: `${family.scratch} scratch, ${family.abandoned} abandoned` },
                  ...(o
                    ? [
                        { label: "Best Sharpe, annual", value: num(o.best_sharpe_annual), note: `luck alone would show ${num(o.expected_max_sharpe_annual)}` },
                        { label: "Deflated Sharpe", value: num(o.deflated_sharpe, 3), note: `before deflating ${num(o.probabilistic_sharpe, 3)}` },
                        { label: "Backtest overfitting", value: o.pbo ? plainPct(o.pbo.pbo) : "–", note: o.pbo ? `${o.pbo.trials_compared} runs, ${o.pbo.splits} splits` : "needs 2+ runs on the same sessions" },
                      ]
                    : []),
                ]}
              />
            </div>
            {o ? (
              <>
                <PanelNote>
                  {o.deflated_sharpe >= 0.95
                    ? "The best run clears the usual 0.95 bar after charging for the trials."
                    : "The best run does not clear the usual 0.95 bar once the trials are charged."}{" "}
                  {o.pbo && `In ${plainPct(o.pbo.pbo)} of the splits, the run that looked best on one half of the sessions landed in the bottom half on the other.`}
                </PanelNote>
                <DataTable
                  rows={sharpes}
                  rowKey={(r) => r.id}
                  columns={[
                    { key: "config", header: "Backtest", align: "left", render: (r) => r.run?.config ?? r.id },
                    { key: "period", header: "Period", align: "left", muted: true, render: (r) => (r.run ? `${r.run.period.start.slice(0, 4)}–${r.run.period.end.slice(0, 4)}` : "") },
                    { key: "agent", header: "Agent", align: "left", muted: true, render: (r) => r.run?.agent ?? "" },
                    { key: "sharpe", header: "Sharpe, annual", signed: true, strong: true, render: (r) => num(r.sharpe) },
                    { key: "best", header: "", align: "left", muted: true, render: (r) => (r.id === o.best_run ? "best" : "") },
                  ]}
                />
              </>
            ) : (
              <PanelNote>No finished backtest in this family yet, so there is no Sharpe to deflate. Studies add to the count but have no daily P&L.</PanelNote>
            )}
          </Panel>
        );
      })}
    </>
  );
}
