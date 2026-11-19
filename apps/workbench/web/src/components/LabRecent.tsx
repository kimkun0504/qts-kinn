import { lab, type RunListRow } from "../lib/lab";
import { href } from "../lib/route";
import { useLoad } from "../lib/useLoad";
import { Card } from "./ui/Card";
import { type Column, DataTable } from "./ui/DataTable";

const SHOWN = 6;
const STATE: Record<RunListRow["state"], string> = { queued: "Waiting", running: "Running", complete: "", failed: "Failed", cancelled: "Cancelled", interrupted: "Interrupted" };

function started(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso.slice(0, 16).replace("T", " ");
  const months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${date.getDate()} ${months[date.getMonth()]} ${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}

const columns: Column<RunListRow>[] = [
  {
    key: "algorithm",
    header: "Algorithm",
    align: "left",
    render: (r) => (
      <a href={href({ page: "lab", name: r.algorithm, tab: r.run_id })} onClick={(event) => event.stopPropagation()} className="font-semibold text-ink no-underline hover:underline">
        {r.algorithm}
      </a>
    ),
  },
  { key: "started", header: "Started", align: "left", muted: true, render: (r) => started(r.created_at) },
  { key: "period", header: "Period", align: "left", muted: true, max: 180, render: (r) => r.period ?? "–" },
  { key: "result", header: "Result", align: "left", max: 380, render: (r) => r.headline ?? (STATE[r.state] || "–") },
  { key: "note", header: "Note", align: "left", muted: true, max: 260, render: (r) => r.note || "–" },
];

export function LabRecent() {
  const { data } = useLoad(() => lab.runs(), "lab-recent");
  if (!data?.length) return null;
  return (
    <Card
      title="Latest Lab runs"
      aside={
        <a href={href({ page: "lab" })} className="font-medium text-accent no-underline hover:underline">
          Open the Lab
        </a>
      }
    >
      <div className="-mx-5 overflow-x-auto">
        <DataTable
          columns={columns}
          rows={data.slice(0, SHOWN)}
          rowKey={(r) => r.run_id}
          onRowClick={(r) => {
            window.location.hash = href({ page: "lab", name: r.algorithm, tab: r.run_id });
          }}
          minWidth={860}
        />
      </div>
    </Card>
  );
}
