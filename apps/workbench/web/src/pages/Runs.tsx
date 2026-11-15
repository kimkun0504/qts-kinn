import { RunsTable } from "../components/RunsTable";
import { Panel } from "../components/ui/Panel";
import { Segmented } from "../components/ui/Segmented";
import type { RunKind, RunRow } from "../lib/api";
import { RunDetail } from "./RunDetail";

export type KindFilter = "all" | RunKind;

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
  const shown = runs.filter((run) => kind === "all" || run.kind === kind);
  return (
    <>
      <Panel
        title={`Runs, newest first (${shown.length})`}
        aside={
          <Segmented
            label="Kind of run"
            value={kind}
            onChange={onKind}
            options={[
              { value: "all", label: "All" },
              { value: "backtest", label: "Backtests" },
              { value: "event_study", label: "Event studies" },
              { value: "tick_study", label: "Tick studies" },
              { value: "book", label: "Books" },
            ]}
          />
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
