import { useEffect, useRef, useState } from "react";
import { RunsTable, runValue } from "../components/RunsTable";
import { isSuccess } from "../components/Verdict";
import { Panel } from "../components/ui/Panel";
import { Segmented } from "../components/ui/Segmented";
import type { RunKind, RunRow } from "../lib/api";
import { sortRows, useSort } from "../lib/sort";
import { RunDetail } from "./RunDetail";

export type KindFilter = "all" | RunKind;
type PhaseFilter = "all" | "development" | "validation" | "holdout";
type ResultFilter = "all" | "success";

interface RunsProps {
  runs: RunRow[];
  selected: string | null;
  onOpen: (run: RunRow) => void;
  compare: string[];
  onToggleCompare: (run: RunRow) => void;
  kind: KindFilter;
  onKind: (kind: KindFilter) => void;
}

export function Runs({ runs, selected, onOpen, compare, onToggleCompare, kind, onKind }: RunsProps) {
  const [phase, setPhase] = useState<PhaseFilter>("all");
  const [result, setResult] = useState<ResultFilter>("all");
  const [strategy, setStrategy] = useState("");
  const [search, setSearch] = useState("");
  const [sort, onSort] = useSort({ key: "started", dir: "desc" });
  const box = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const row = box.current?.querySelector<HTMLElement>('tr[aria-selected="true"]');
    if (box.current && row) box.current.scrollTop = Math.max(0, row.offsetTop - box.current.clientHeight / 3);
  }, [selected]);
  const names = [...new Set(runs.map((run) => run.strategy))].sort();
  const words = search.trim().toLowerCase().split(/\s+/).filter(Boolean);
  const text = (run: RunRow) => [run.run_id, run.strategy, run.config, run.agent, run.kind, run.branch, run.commit].join(" ").toLowerCase();
  const shown = sortRows(
    runs.filter(
      (run) =>
        (kind === "all" || run.kind === kind) &&
        (phase === "all" || run.phase === phase) &&
        (result === "all" || isSuccess(run)) &&
        (!strategy || run.strategy === strategy) &&
        words.every((w) => text(run).includes(w)),
    ),
    sort,
    runValue,
  );
  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
        <input
          type="search"
          aria-label="Find runs"
          placeholder="Strategy, config, agent or run id"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="min-h-8 w-64 rounded-md border border-line bg-surface px-2.5 text-[13px] text-ink placeholder:text-ink-3 focus:border-accent focus:outline-none"
        />
        <label className="inline-flex items-center gap-2">
          <span className="sr-only">Strategy</span>
          <select
            value={strategy}
            onChange={(event) => setStrategy(event.target.value)}
            className="min-h-8 cursor-pointer rounded-md border border-line bg-surface px-2 text-[13px] font-medium text-ink focus-visible:outline-2 focus-visible:outline-accent"
          >
            <option value="">Every strategy</option>
            {names.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </label>
        <Segmented
          label="Result"
          value={result}
          onChange={setResult}
          options={[
            { value: "all", label: "All results" },
            { value: "success", label: "Met every target" },
          ]}
        />
        <Segmented
          label="Research period"
          value={phase}
          onChange={setPhase}
          options={[
            { value: "all", label: "Any period" },
            { value: "development", label: "Development" },
            { value: "validation", label: "Validation" },
            { value: "holdout", label: "Holdout" },
          ]}
        />
        <Segmented
          label="Kind of run"
          value={kind}
          onChange={onKind}
          options={[
            { value: "all", label: "All" },
            { value: "backtest", label: "Backtests" },
            { value: "swing", label: "Swing" },
            { value: "event_study", label: "Event studies" },
            { value: "fill_check", label: "Fill checks" },
            { value: "tick_study", label: "Tick studies" },
            { value: "book", label: "Books" },
          ]}
        />
      </div>
      <Panel title={`${shown.length} of ${runs.length} runs`} aside={selected ? "The selected run is in the address bar, so a link opens it" : "Click a run to see its results"}>
        <div ref={box} className="max-h-[max(360px,50vh)] overflow-y-auto">
          <RunsTable runs={shown} onOpen={onOpen} selected={selected} compare={compare} onToggleCompare={onToggleCompare} sort={sort} onSort={onSort} />
        </div>
      </Panel>
      <RunDetail runId={selected} />
    </>
  );
}
