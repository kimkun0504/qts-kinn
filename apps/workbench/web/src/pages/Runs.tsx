import { useState } from "react";
import { RunsTable } from "../components/RunsTable";
import { isSuccess } from "../components/Verdict";
import { Panel } from "../components/ui/Panel";
import { Segmented } from "../components/ui/Segmented";
import type { RunKind, RunRow } from "../lib/api";
import { RunDetail } from "./RunDetail";

export type KindFilter = "all" | RunKind;
type PhaseFilter = "all" | "development" | "validation";
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
  const shown = runs.filter(
    (run) => (kind === "all" || run.kind === kind) && (phase === "all" || run.phase === phase) && (result === "all" || isSuccess(run)),
  );
  return (
    <>
      <Panel
        title={`Runs, newest first (${shown.length})`}
        aside={
          <div className="flex flex-wrap items-center justify-end gap-2">
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
              ]}
            />
            <Segmented
              label="Kind of run"
              value={kind}
              onChange={onKind}
              options={[
                { value: "all", label: "All" },
                { value: "backtest", label: "Backtests" },
                { value: "event_study", label: "Event studies" },
                { value: "fill_check", label: "Fill checks" },
                { value: "tick_study", label: "Tick studies" },
                { value: "book", label: "Books" },
              ]}
            />
          </div>
        }
      >
        <div className="max-h-[330px] overflow-y-auto">
          <RunsTable runs={shown} onOpen={onOpen} selected={selected} compare={compare} onToggleCompare={onToggleCompare} />
        </div>
      </Panel>
      <RunDetail runId={selected} />
    </>
  );
}
