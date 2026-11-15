import type { RunRow } from "../lib/api";
import { int, num, pct, shortTime } from "../lib/format";
import { type Column, DataTable } from "./ui/DataTable";

const KIND: Record<string, string> = { backtest: "Backtest", event_study: "Event study", tick_study: "Tick study" };

function notes(run: RunRow): string {
  return [
    run.scratch ? "scratch" : "",
    run.status !== "complete" ? run.status : "",
    run.dirty ? "uncommitted code" : "",
    run.schema_ok ? "" : "unknown schema",
  ]
    .filter(Boolean)
    .join(", ");
}

interface RunsTableProps {
  runs: RunRow[];
  onOpen: (run: RunRow) => void;
  selected?: string | null;
  compare?: string[];
  onToggleCompare?: (run: RunRow) => void;
  compact?: boolean;
}

/** The runs list used on the overview (compact) and on the runs page (full). */
export function RunsTable({ runs, onOpen, selected, compare, onToggleCompare, compact = false }: RunsTableProps) {
  const columns: Column<RunRow>[] = [];
  if (onToggleCompare) {
    columns.push({
      key: "compare",
      header: "Compare",
      align: "left",
      render: (run) =>
        run.kind === "backtest" && run.status === "complete" ? (
          <input
            type="checkbox"
            aria-label={`Compare ${run.config}`}
            checked={compare?.includes(run.run_id) ?? false}
            onClick={(event) => event.stopPropagation()}
            onChange={() => onToggleCompare(run)}
          />
        ) : null,
    });
  }
  columns.push(
    { key: "started", header: "Started (UTC)", align: "left", muted: true, render: (run) => shortTime(run.started_at) },
    { key: "strategy", header: "Strategy", align: "left", strong: true, render: (run) => run.strategy },
    { key: "config", header: "Config", align: "left", muted: true, render: (run) => run.config },
    { key: "kind", header: "Kind", align: "left", render: (run) => KIND[run.kind] ?? run.kind },
  );
  if (!compact) columns.push({ key: "agent", header: "Agent", align: "left", muted: true, render: (run) => run.agent });
  columns.push(
    { key: "trades", header: "Trades", render: (run) => int(run.trades) },
    { key: "net1", header: "Net 1×", signed: true, strong: true, render: (run) => pct(run.net_1x) },
    { key: "net2", header: "Net 2×", signed: true, render: (run) => pct(run.net_2x) },
  );
  if (!compact) {
    columns.push(
      { key: "gross", header: "Gross", signed: true, render: (run) => pct(run.gross) },
      { key: "t2", header: "t at 2×", signed: true, render: (run) => num(run.t_stat_2x) },
      { key: "notes", header: "Notes", align: "left", muted: true, render: notes },
    );
  }
  return (
    <DataTable
      columns={columns}
      rows={runs}
      rowKey={(run) => run.run_id}
      onRowClick={onOpen}
      selectedKey={selected}
      minWidth={compact ? 620 : 980}
      empty="No runs yet. Start one with: uv run kinn run <strategy> --config <name>"
    />
  );
}
