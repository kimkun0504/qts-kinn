import { useState } from "react";
import { RunsTable } from "../components/RunsTable";
import { isSuccess } from "../components/Verdict";
import { Panel } from "../components/ui/Panel";
import { Segmented } from "../components/ui/Segmented";
import type { RunKind, RunRow } from "../lib/api";
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
  const names = [...new Set(runs.map((run) => run.strategy))].sort();
  const shown = runs.filter(
    (run) =>
      (kind === "all" || run.kind === kind) && (phase === "all" || run.phase === phase) && (result === "all" || isSuccess(run)) && (!strategy || run.strategy === strategy),
  );
  return (
    <>
      <div className="flex flex-wrap items-center gap-2">
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
      <Panel title={`${shown.length} run${shown.length === 1 ? "" : "s"}, newest first`}>
        <div className="max-h-[max(330px,44vh)] overflow-y-auto">
          <RunsTable runs={shown} onOpen={onOpen} selected={selected} compare={compare} onToggleCompare={onToggleCompare} />
        </div>
      </Panel>
      <RunDetail runId={selected} />
    </>
  );
}
