import { useState } from "react";
import { api, type LedgerEvening, type LedgerPage, type LedgerRow } from "../lib/api";
import { day, int, money, num, pct } from "../lib/format";
import { sortRows, useSort } from "../lib/sort";
import { useLoad } from "../lib/useLoad";
import { LineChart } from "./charts/LineChart";
import { CsvButton } from "./CsvButton";
import { StockLink } from "./StockLink";
import { Badge } from "./ui/Badge";
import { Card, Note } from "./ui/Card";
import { type Column, DataTable } from "./ui/DataTable";
import { EmptyState } from "./ui/EmptyState";
import { Segmented } from "./ui/Segmented";
import { StatStrip, type StatItem } from "./ui/StatStrip";

type Show = "all" | "open" | "closed" | "aside";

const price = (value: number | null | undefined) => (value == null ? "–" : `$${value.toFixed(2)}`);
const millions = (value: number | null | undefined) => (value ? `$${Math.round(value / 1e6).toLocaleString("en-US")}M` : "–");
const times = (value: number | null | undefined) => (value == null ? "–" : `${value.toFixed(1)}×`);

export function stamp(iso: string): string {
  return new Date(iso).toLocaleString("en-US", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", hour12: false });
}

function status(row: LedgerRow): string {
  if (row.set_aside) return "Set aside";
  if (row.status === "waiting") return "Waiting for the open";
  return row.status === "open" ? "Open" : "Closed";
}

function behind(last: string | null): number {
  if (!last) return 0;
  const today = new Date();
  let days = 0;
  const cursor = new Date(`${last}T12:00:00`);
  while (cursor < today) {
    cursor.setDate(cursor.getDate() + 1);
    if (cursor.getDay() !== 0 && cursor.getDay() !== 6 && cursor < today) days += 1;
  }
  return Math.max(0, days - 1);
}

function columns(page: LedgerPage): Column<LedgerRow>[] {
  const head: Column<LedgerRow>[] = [
    { key: "day", header: page.side === "short" ? "Evening" : "Day", align: "left", sortable: true, render: (r) => day(r.day, true) },
    { key: "symbol", header: "Stock", align: "left", sortable: true, render: (r) => <StockLink symbol={r.symbol} /> },
    { key: "market_cap", header: "Value", sortable: true, render: (r) => millions(r.market_cap) },
  ];
  const tail: Column<LedgerRow>[] = [
    { key: "net", header: "After costs", sortable: true, signed: true, strong: true, render: (r) => pct(r.net) },
    { key: "alternative", header: page.alternative, sortable: true, signed: true, render: (r) => pct(r.alternative) },
  ];
  if (page.side === "short") {
    return [
      ...head,
      { key: "accepted", header: "Filed", sortable: true, muted: true, render: (r) => r.accepted ?? "–" },
      { key: "move", header: "After hours", sortable: true, signed: true, render: (r) => pct(r.move, 1) },
      { key: "entry", header: "Sold at", render: (r) => price(r.entry) },
      { key: "thin", header: "Thin minute", sortable: true, render: (r) => (r.thin ? "yes" : "no") },
      { key: "exit", header: "Next open", render: (r) => price(r.exit) },
      ...tail,
      { key: "borrow", header: "Borrow (IBKR)", align: "left", sortable: true, muted: true, render: (r) => r.borrow ?? "not recorded" },
    ];
  }
  return [
    ...head,
    { key: "footprint", header: "Trade size", sortable: true, render: (r) => times(r.footprint) },
    { key: "move", header: "Up", sortable: true, signed: true, render: (r) => pct(r.move, 1) },
    { key: "volume_ratio", header: "Volume", sortable: true, render: (r) => times(r.volume_ratio) },
    { key: "entry", header: "Bought", render: (r) => (r.entry == null ? "–" : `${day(r.entry_day, true)} ${price(r.entry)}`) },
    { key: "exit", header: "Sold", render: (r) => (r.exit == null ? "–" : `${day(r.exit_day, true)} ${price(r.exit)}${r.stopped ? " stopped" : ""}`) },
    ...tail,
    { key: "benchmark", header: page.benchmark ?? "Index", sortable: true, signed: true, muted: true, render: (r) => pct(r.benchmark) },
    { key: "status", header: "Status", align: "left", sortable: true, muted: true, render: status },
  ];
}

function value(row: LedgerRow, key: string) {
  if (key === "status") return status(row);
  return row[key as keyof LedgerRow] as string | number | boolean | null | undefined;
}

function Evenings({ page }: { page: LedgerPage }) {
  const short = page.side === "short";
  const cols: Column<LedgerEvening>[] = [
    { key: "day", header: short ? "Evening" : "Day", align: "left", render: (e) => day(e.day, true) },
    ...(short ? [{ key: "filers", header: "8-K filers", render: (e: LedgerEvening) => int(e.filers) }] : []),
    { key: "looked", header: short ? "Results 8-Ks" : "Screened", render: (e) => int(e.looked_at) },
    { key: "signals", header: "Signals", strong: true, render: (e) => int(e.signals) },
    { key: "note", header: "", align: "left", muted: true, render: (e) => e.note ?? "" },
  ];
  return <DataTable columns={cols} rows={page.evening_rows} rowKey={(e) => e.day} />;
}

function Curve({ page }: { page: LedgerPage }) {
  if (page.curve.length < 2) return <p className="m-0 py-6 text-ink-2">{page.curve.length ? "One closed trade so far." : "No closed trade yet."}</p>;
  const points = [{ day: page.curve[0].day, symbol: "Start", total: 0 }, ...page.curve];
  const few = points.length <= 12;
  return (
    <LineChart
      title="Cumulative profit"
      labels={points.map((p) => (few ? p.symbol : p.day))}
      everyLabel={few}
      series={[{ name: "Profit", values: points.map((p) => p.total), color: "var(--series-1)" }]}
      format={money}
      height={220}
    />
  );
}

export function LedgerView({ name }: { name: string }) {
  const { data: page, error } = useLoad(() => api.ledger(name), name);
  const [show, setShow] = useState<Show>("all");
  const [sort, onSort] = useSort({ key: "day", dir: "desc" });
  if (error) return <EmptyState title="This ledger could not be read">Restart the Workbench server after updating, then reload.</EmptyState>;
  if (!page) return <p className="text-ink-2">Loading the ledger…</p>;
  const s = page.summary;
  const late = behind(page.last_evening);
  const items: StatItem[] = [
    { label: "Signals", value: int(s.signals), note: `${s.closed} closed, ${s.open + s.waiting} open` },
    { label: "A trade after costs", value: pct(s.mean), note: s.closed ? `${s.winners} of ${s.closed} made money` : "none closed yet" },
    { label: "Profit", value: money(s.closed ? s.profit : null), note: `$${num(page.stake, 0)} a trade` },
    { label: page.alternative, value: pct(s.alternative), note: s.alternative_count ? `on ${s.alternative_count}` : "none yet" },
    page.benchmark
      ? { label: `Over ${page.benchmark}`, value: pct(s.over_benchmark), note: "same days" }
      : { label: "Borrow recorded", value: `${s.borrow_recorded} of ${s.signals}`, note: "from IBKR" },
  ];
  const aside = page.rows.filter((r) => r.set_aside);
  const shown = page.rows.filter((r) =>
    show === "aside" ? r.set_aside : show === "all" ? !r.set_aside : !r.set_aside && (show === "closed" ? r.status === "closed" : r.status !== "closed"),
  );
  const options: { value: Show; label: string }[] = [
    { value: "all", label: `All ${s.signals}` },
    { value: "open", label: `Open ${s.open + s.waiting}` },
    { value: "closed", label: `Closed ${s.closed}` },
    ...(aside.length ? [{ value: "aside" as Show, label: `Set aside ${aside.length}` }] : []),
  ];
  return (
    <>
      <div className="flex flex-col gap-2">
        <p className="m-0 max-w-[90ch] text-ink-2">{page.rule}</p>
        <div className="flex flex-wrap items-center gap-x-5 gap-y-1 text-[13px] text-ink-3">
          {late > 0 ? <Badge tone="warn">{`Behind: last evening ${day(page.last_evening, true)}`}</Badge> : <Badge tone="ok">{`Up to ${day(page.last_evening, true)}`}</Badge>}
          <span>{page.evenings} evenings recorded</span>
          <span>File updated {stamp(page.updated)}</span>
          <span>Paper only; no order is sent anywhere</span>
        </div>
      </div>
      <StatStrip items={items} />
      <div className="grid items-start gap-5 lg:grid-cols-[minmax(0,1.6fr)_minmax(0,1fr)]">
        <Card title={`Cumulative profit, $${num(page.stake, 0)} a trade`} aside="Closed trades in the order they closed">
          <Curve page={page} />
        </Card>
        <Card title="Evenings" aside={page.schedule}>
          <div className="-mx-5 max-h-[260px] overflow-y-auto">
            <Evenings page={page} />
          </div>
          <Note>
            Updated by <code className="font-mono text-[12px]">{page.command}</code>
          </Note>
        </Card>
      </div>
      <Card
        title="Signals"
        aside={
          <div className="flex flex-wrap items-center gap-2">
            <Segmented label="Which signals" options={options} value={show} onChange={setShow} />
            <CsvButton
              filename={`${page.name}_signals.csv`}
              rows={page.rows}
              columns={[
                { header: "day", value: (r) => r.day },
                { header: "symbol", value: (r) => r.symbol },
                { header: "market_cap", value: (r) => r.market_cap },
                { header: "move", value: (r) => r.move },
                { header: "entry_day", value: (r) => r.entry_day },
                { header: "entry", value: (r) => r.entry },
                { header: "exit_day", value: (r) => r.exit_day },
                { header: "exit", value: (r) => r.exit },
                { header: "gross", value: (r) => r.gross },
                { header: "net", value: (r) => r.net },
                { header: "alternative", value: (r) => r.alternative },
                { header: "benchmark", value: (r) => r.benchmark },
                { header: "status", value: (r) => r.status },
                { header: "set_aside", value: (r) => r.set_aside },
                { header: "borrow", value: (r) => r.borrow },
              ]}
            />
          </div>
        }
      >
        <div className="-mx-5 overflow-x-auto">
          <DataTable columns={columns(page)} rows={sortRows(shown, sort, value)} rowKey={(r) => `${r.day}-${r.symbol}`} sort={sort} onSort={onSort} minWidth={1000} empty="No signal here yet." />
        </div>
        {page.side === "short" && <Note>Record what IBKR showed for each signal with --borrow SYMBOL="yes, 0.3%" on the ledger's command. A thin minute traded under $5,000, so its low is a doubtful fill.</Note>}
        {aside.length > 0 && show === "aside" && (
          <Note>
            Signals on index days, when 5% or more of stocks traded in large pieces: kept apart from the rule. {s.set_aside_closed} closed, {pct(s.set_aside_mean)} a trade.
          </Note>
        )}
      </Card>
    </>
  );
}
