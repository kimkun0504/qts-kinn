import { useMemo, useState } from "react";
import { DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { Panel, PanelNote } from "../components/ui/Panel";
import { StatStrip } from "../components/ui/StatStrip";
import type { Family, RunRow } from "../lib/api";
import { int, num, plainPct } from "../lib/format";
import { lab } from "../lib/lab";
import { href } from "../lib/route";
import { type SortValue, sortRows, useSort } from "../lib/sort";
import { useLoad } from "../lib/useLoad";

function familyValue(family: Family, key: string): SortValue {
  const o = family.overfitting;
  if (key === "family") return family.family;
  if (key === "trials") return family.trials;
  if (key === "counted") return family.counted;
  if (key === "best") return o?.best_sharpe_annual;
  if (key === "deflated") return o?.deflated_sharpe;
  if (key === "pbo") return o?.pbo?.pbo;
  return null;
}

function LabTrials() {
  const { data } = useLoad(() => lab.algorithms(), "lab-trials");
  if (!data?.length) return null;
  return (
    <Panel title={`Lab algorithms, ${int(data.reduce((sum, a) => sum + a.trials, 0))} trials`} aside="each run that computed signals is one; a sweep counts each value">
      <DataTable
        rows={data}
        rowKey={(a) => a.name}
        onRowClick={(a) => {
          window.location.hash = href({ page: "lab", name: a.name });
        }}
        columns={[
          { key: "name", header: "Algorithm", align: "left", strong: true, render: (a) => a.name },
          { key: "description", header: "What it does", align: "left", muted: true, max: 420, render: (a) => a.description || "–" },
          { key: "runs", header: "Runs", render: (a) => int(a.runs) },
          { key: "trials", header: "Trials", strong: true, render: (a) => int(a.trials) },
        ]}
      />
    </Panel>
  );
}

export function Trials({ families, runs }: { families: Family[]; runs: RunRow[] }) {
  const [sort, onSort] = useSort({ key: "trials", dir: "desc" });
  const ordered = useMemo(() => sortRows(families, sort, familyValue), [families, sort]);
  const [chosen, setChosen] = useState<string | null>(null);
  if (!families.length) return <EmptyState title="No runs yet" />;
  const open = chosen ?? ordered[0]?.family;
  return (
    <>
      <StatStrip
        items={[
          { label: "Trials charged", value: int(families.reduce((sum, f) => sum + f.trials, 0)), note: `across ${families.length} families` },
          { label: "Counted runs", value: int(families.reduce((sum, f) => sum + f.counted, 0)) },
          { label: "Families with a deflated Sharpe", value: int(families.filter((f) => f.overfitting).length) },
          { label: "Clearing 0.95 deflated", value: int(families.filter((f) => (f.overfitting?.deflated_sharpe ?? 0) >= 0.95).length) },
        ]}
      />
      <Panel title="Families">
        <div className="max-h-[420px] overflow-y-auto">
          <DataTable
            rows={ordered}
            rowKey={(f) => f.family}
            selectedKey={open}
            onRowClick={(f) => setChosen(f.family)}
            sort={sort}
            onSort={onSort}
            columns={[
              { key: "family", header: "Family", align: "left", strong: true, sortable: true, render: (f) => f.family },
              { key: "trials", header: "Trials charged", sortable: true, render: (f) => int(f.trials) },
              { key: "counted", header: "Counted runs", sortable: true, render: (f) => int(f.counted) },
              { key: "best", header: "Best Sharpe", sortable: true, signed: true, render: (f) => (f.overfitting ? num(f.overfitting.best_sharpe_annual) : "–") },
              { key: "deflated", header: "Deflated Sharpe", sortable: true, render: (f) => (f.overfitting ? num(f.overfitting.deflated_sharpe, 3) : "–") },
              { key: "pbo", header: "Overfitting", sortable: true, render: (f) => (f.overfitting?.pbo ? plainPct(f.overfitting.pbo.pbo) : "–") },
            ]}
          />
        </div>
      </Panel>
      {families
        .filter((family) => family.family === open)
        .map((family) => {
          const o = family.overfitting;
          const agents =
            Object.entries(family.by_agent)
              .map(([agent, n]) => `${agent} ${n}`)
              .join(", ") || "none";
          const sharpes = o
            ? Object.entries(o.sharpes)
                .map(([id, sharpe]) => ({ id, sharpe, run: runs.find((r) => r.run_id === id) }))
                .sort((a, b) => b.sharpe - a.sharpe)
            : [];
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
                          {
                            label: "Backtest overfitting",
                            value: o.pbo ? plainPct(o.pbo.pbo) : "–",
                            note: o.pbo ? `${o.pbo.trials_compared} runs, ${o.pbo.splits} splits` : "needs 2+ runs on the same sessions",
                          },
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
      <LabTrials />
    </>
  );
}
