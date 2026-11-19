import { Bars } from "../components/ui/Bars";
import { Card, Note } from "../components/ui/Card";
import { type Column, DataTable } from "../components/ui/DataTable";
import { EmptyState } from "../components/ui/EmptyState";
import { StatStrip } from "../components/ui/StatStrip";
import { api, type DataCatalog } from "../lib/api";
import { compact, day, int } from "../lib/format";
import { useLoad } from "../lib/useLoad";
import { stamp } from "../components/LedgerView";

type Table = DataCatalog["tables"][number];
type Input = DataCatalog["inputs"][number];

const SPLIT_LABELS: Record<string, string> = {
  listed: "listed by the vendor",
  date_moved: "moved to the day prices show it",
  dropped_no_price_change: "dropped: prices never changed",
  no_bars_nearby: "no bars near the date",
  too_small_to_check: "too small to check",
};

function bytes(value: number): string {
  if (value >= 1e9) return `${(value / 1e9).toFixed(1)} GB`;
  if (value >= 1e6) return `${Math.round(value / 1e6)} MB`;
  return `${Math.max(1, Math.round(value / 1e3))} KB`;
}

const tableColumns: Column<Table>[] = [
  { key: "name", header: "Table", align: "left", strong: true, render: (t) => t.name },
  { key: "note", header: "What it holds", align: "left", muted: true, render: (t) => t.note },
  { key: "rows", header: "Rows", render: (t) => (t.rows == null ? "–" : compact(t.rows)) },
  { key: "files", header: "Files", render: (t) => int(t.files) },
  { key: "bytes", header: "Size", render: (t) => bytes(t.bytes) },
];

const inputColumns: Column<Input>[] = [
  { key: "name", header: "Input", align: "left", strong: true, render: (i) => i.name },
  { key: "version", header: "Version", align: "left", muted: true, render: (i) => (i.built ? `${i.version ?? "–"} (${i.input_id ?? "–"})` : "not built") },
  { key: "rows", header: "Rows", render: (i) => (i.rows == null ? "–" : compact(i.rows)) },
  { key: "span", header: "Covers", render: (i) => (i.first ? `${day(i.first)} to ${day(i.last)}` : "–") },
  { key: "built", header: "Built", muted: true, render: (i) => (i.built_at ? stamp(i.built_at) : "–") },
];

export function DataPage() {
  const { data, error } = useLoad(() => api.data(), "data");
  if (error) return <EmptyState title="The data catalog could not be read">Restart the Workbench server after updating; it needs a data build.</EmptyState>;
  if (!data) return <p className="text-ink-2">Reading the build…</p>;
  const splits = Object.entries(data.build.panel.splits ?? {});
  return (
    <>
      <StatStrip
        items={[
          { label: "Data build", value: data.build.id, note: `${data.build.data_version ?? ""}, built ${data.build.created_at ? stamp(data.build.created_at) : "–"}` },
          { label: "Sessions", value: int(data.calendar.sessions), note: `${day(data.calendar.first)} to ${day(data.calendar.last)}` },
          { label: "Companies", value: int(data.companies.total), note: `${int(data.companies.delisted)} delisted, kept to avoid survivor bias` },
          { label: "Daily rows", value: compact(data.build.panel.panel_rows ?? null), note: "company-sessions in the panel" },
          { label: "Holdout", value: `From ${day(data.seal.holdout_start, true)} ${data.seal.holdout_start.slice(0, 4)}`, note: `sealed; ${int(data.seal.reads)} owner reads logged` },
        ]}
      />
      <Card title="Tables in this build" aside={`Vendor snapshot ${day(data.build.sharadar_snapshot)}`}>
        <div className="-mx-5 overflow-x-auto">
          <DataTable columns={tableColumns} rows={data.tables} rowKey={(t) => t.name} minWidth={760} />
        </div>
      </Card>
      <div className="grid items-start gap-5 lg:grid-cols-2">
        <Card title="Price bars" aside={`bars ${data.build.bars_id ?? ""}`}>
          <dl className="m-0 grid grid-cols-[auto_1fr] gap-x-6 gap-y-2 text-sm">
            {data.bars.map((b) => (
              <div key={b.name} className="contents">
                <dt className="font-medium">{b.name[0].toUpperCase() + b.name.slice(1)}</dt>
                <dd className="m-0 text-ink-2">
                  {b.years.length ? `${b.years[0]} to ${b.years[b.years.length - 1]}, ${int(b.files)} yearly files` : `${int(b.files)} files`}
                </dd>
              </div>
            ))}
          </dl>
          {splits.length > 0 && (
            <>
              <h3 className="m-0 mt-2 text-[13px] font-semibold text-ink-2">Splits, as the build checked them</h3>
              <dl className="m-0 grid grid-cols-[auto_1fr] gap-x-6 gap-y-1 text-sm">
                {splits.map(([key, n]) => (
                  <div key={key} className="contents">
                    <dt className="text-right tabular-nums">{int(n)}</dt>
                    <dd className="m-0 text-ink-2">{SPLIT_LABELS[key] ?? key.replace(/_/g, " ")}</dd>
                  </div>
                ))}
              </dl>
            </>
          )}
        </Card>
        <Card title="Versioned inputs">
          <div className="-mx-5 overflow-x-auto">
            <DataTable columns={inputColumns} rows={data.inputs} rowKey={(i) => i.name} minWidth={560} />
          </div>
          {data.inputs.some((i) => i.basis) && <Note>8-K times: {data.inputs.find((i) => i.basis)?.basis}.</Note>}
        </Card>
      </div>
      <div className="grid items-start gap-5 lg:grid-cols-2">
        <Card title="Companies by kind">
          <Bars items={data.companies.categories} total={data.companies.total} />
        </Card>
        <Card title="Companies by sector">
          <Bars items={data.companies.sectors} total={data.companies.total} />
        </Card>
      </div>
      <Card title="Builds" aside="Each build is kept; runs record the one they read">
        <div className="-mx-5 overflow-x-auto">
          <DataTable
            columns={[
              { key: "id", header: "Build", align: "left", strong: true, render: (b) => b.id },
              { key: "version", header: "Version", align: "left", muted: true, render: (b) => b.data_version ?? "–" },
              { key: "bars", header: "Bars", align: "left", muted: true, render: (b) => b.bars_id ?? "–" },
              { key: "created", header: "Built", render: (b) => (b.created_at ? stamp(b.created_at) : "–") },
              { key: "current", header: "", align: "left", render: (b) => (b.current ? "current" : "") },
            ]}
            rows={data.builds}
            rowKey={(b) => b.id}
            selectedKey={data.builds.find((b) => b.current)?.id}
          />
        </div>
      </Card>
      <Note>
        The research reads this build through the sealed store: nothing from {day(data.seal.holdout_start)} on. The paper ledgers read live prices from Massive and filings from the SEC, outside it.
        {data.seal.last ? ` Last owner read of the holdout logged ${stamp(data.seal.last)}.` : ""}
      </Note>
    </>
  );
}
